import asyncio
import logging
import uuid
from pathlib import Path

from aiogram import Bot, F, Router
from aiogram.enums import ChatAction
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from config import settings
from converter import ConversionError, convert_to_video_note
from locales import t
from storage import get_user_language, set_user_language

logger = logging.getLogger(__name__)
router = Router(name="media_router")

task_semaphore = asyncio.Semaphore(settings.max_concurrent_tasks)

SUPPORTED_EXTENSIONS = (
    ".mp4",
    ".mov",
    ".webm",
    ".mkv",
    ".avi",
    ".flv",
    ".wmv",
    ".m4v",
    ".gif",
    ".3gp",
)


def get_sender_id(message: Message) -> int:
    return message.from_user.id if message.from_user else message.chat.id


def build_language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="English", callback_data="lang:en"),
                InlineKeyboardButton(text="Русский", callback_data="lang:ru"),
            ]
        ]
    )


@router.message(CommandStart())
async def handle_start(message: Message) -> None:
    user_id = get_sender_id(message)
    current_lang = await get_user_language(user_id)

    # Prompt language selection only on the first start
    if current_lang is None:
        prompt_text = "Choose your interface language / Выберите язык интерфейса:"
        await message.reply(prompt_text, reply_markup=build_language_keyboard())
        return

    welcome_text = t("start", current_lang, max_mb=settings.max_file_size_mb)
    await message.reply(welcome_text)


@router.message(Command("language", "lang"))
async def handle_language_command(message: Message) -> None:
    user_id = get_sender_id(message)
    user_lang = await get_user_language(user_id)
    prompt_text = t("select_language", user_lang)
    await message.reply(prompt_text, reply_markup=build_language_keyboard())


@router.callback_query(F.data.startswith("lang:"))
async def handle_language_selection(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id if callback.from_user else (callback.message.chat.id if callback.message else 0)
    selected_language = callback.data.split(":", 1)[1]
    if selected_language not in ("en", "ru"):
        selected_language = "en"

    await set_user_language(user_id, selected_language)
    await callback.answer()

    confirmation_text = t("language_saved", selected_language)
    welcome_text = t("start", selected_language, max_mb=settings.max_file_size_mb)
    response_content = f"{confirmation_text}\n\n{welcome_text}"

    if callback.message:
        await callback.message.edit_text(response_content)


@router.message(Command("help"))
async def handle_help(message: Message) -> None:
    user_id = get_sender_id(message)
    user_lang = await get_user_language(user_id)
    help_text = t("help", user_lang)
    await message.reply(help_text)


def extract_media(message: Message):
    if message.video:
        return message.video
    if message.animation:
        return message.animation
    if message.video_note:
        return message.video_note
    if message.document:
        mime = (message.document.mime_type or "").lower()
        file_name = (message.document.file_name or "").lower()
        if mime.startswith("video/") or mime == "image/gif" or file_name.endswith(SUPPORTED_EXTENSIONS):
            return message.document
    return None


@router.message(F.video | F.animation | F.document | F.video_note)
async def handle_incoming_media(message: Message, bot: Bot) -> None:
    user_id = get_sender_id(message)
    user_lang = await get_user_language(user_id)
    media_item = extract_media(message)

    if not media_item:
        if message.document:
            await message.reply(t("unsupported_document", user_lang))
        return

    max_bytes = settings.max_file_size_mb * 1024 * 1024
    if media_item.file_size and media_item.file_size > max_bytes:
        await message.reply(t("file_too_large", user_lang, max_mb=settings.max_file_size_mb))
        return

    temp_folder = settings.ensure_temp_dir()
    file_token = uuid.uuid4().hex
    source_file = temp_folder / f"input_{file_token}.tmp"
    target_file = temp_folder / f"output_{file_token}.mp4"

    status_message = await message.reply(t("downloading", user_lang))

    try:
        # Wrap download and conversion inside semaphore to bound both disk and CPU consumption
        async with task_semaphore:
            await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.RECORD_VIDEO_NOTE)
            await bot.download(media_item, destination=source_file)

            await status_message.edit_text(t("converting", user_lang))

            duration_seconds = await convert_to_video_note(
                source_path=source_file,
                target_path=target_file,
                resolution=settings.target_resolution,
                max_duration_seconds=settings.max_duration_seconds,
            )

        await status_message.edit_text(t("uploading", user_lang))
        await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.UPLOAD_VIDEO_NOTE)

        await message.reply_video_note(
            video_note=FSInputFile(path=target_file),
            duration=duration_seconds,
            length=settings.target_resolution,
        )
        await status_message.delete()

    except ConversionError as exc:
        logger.error(f"Conversion error for user {user_id}: {exc}")
        await status_message.edit_text(t("conversion_error", user_lang))
    except Exception as exc:
        logger.exception(f"Unexpected error processing media from user {user_id}: {exc}")
        await status_message.edit_text(t("unexpected_error", user_lang))
    finally:
        source_file.unlink(missing_ok=True)
        target_file.unlink(missing_ok=True)
