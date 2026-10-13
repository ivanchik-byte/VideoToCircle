import asyncio
import json
import sqlite3
import subprocess
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from config import Settings
from converter import check_audio_stream, convert_to_video_note, get_video_duration
from handlers import extract_media, get_sender_id
from locales import t
from storage import get_user_language, init_db, set_user_language


def probe_file(file_path: Path) -> dict:
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_streams",
        "-show_format",
        "-of", "json",
        str(file_path),
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
    return json.loads(res.stdout)


@pytest.mark.asyncio
async def test_storage_isolated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    test_db = tmp_path / "test_users.db"
    monkeypatch.setattr("storage.get_db_path", lambda: test_db)

    init_db()
    test_user_id = 12345

    assert await get_user_language(test_user_id) is None

    await set_user_language(test_user_id, "ru")
    assert await get_user_language(test_user_id) == "ru"

    await set_user_language(test_user_id, "en")
    assert await get_user_language(test_user_id) == "en"


def test_locales() -> None:
    ru_start = t("start", "ru", max_mb=1000)
    en_start = t("start", "en", max_mb=1000)
    fallback = t("start", "unknown", max_mb=1000)

    assert "квадрат" in ru_start
    assert "square" in en_start
    assert fallback == en_start


def test_extract_media_and_sender_guard() -> None:
    msg = MagicMock()
    msg.from_user = None
    msg.chat.id = 98765
    assert get_sender_id(msg) == 98765

    msg.from_user = MagicMock()
    msg.from_user.id = 112233
    assert get_sender_id(msg) == 112233

    # Video extraction
    msg.video = MagicMock()
    msg.animation = None
    msg.video_note = None
    msg.document = None
    assert extract_media(msg) == msg.video

    # Document filtering
    msg.video = None
    msg.document = MagicMock()
    msg.document.mime_type = "application/pdf"
    msg.document.file_name = "test.pdf"
    assert extract_media(msg) is None

    msg.document.mime_type = "video/mp4"
    msg.document.file_name = "clip.mp4"
    assert extract_media(msg) == msg.document


@pytest.mark.asyncio
async def test_video_conversion_with_audio(tmp_path: Path) -> None:
    input_file = tmp_path / "in_audio.mp4"
    output_file = tmp_path / "out_audio.mp4"

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "testsrc=duration=2:size=1280x720:rate=30",
        "-f", "lavfi", "-i", "sine=frequency=1000:duration=2",
        "-c:v", "libx264", "-c:a", "aac",
        str(input_file)
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    assert await check_audio_stream(input_file) is True

    duration = await convert_to_video_note(input_file, output_file, resolution=480, max_duration_seconds=60)
    assert duration > 0

    meta = probe_file(output_file)
    v_stream = next(s for s in meta["streams"] if s["codec_type"] == "video")
    a_stream = next(s for s in meta["streams"] if s["codec_type"] == "audio")

    assert v_stream["width"] == 480 and v_stream["height"] == 480
    assert v_stream["pix_fmt"] == "yuv420p"
    assert a_stream["codec_name"] == "aac"


@pytest.mark.asyncio
async def test_video_conversion_silent_and_duration_clamp(tmp_path: Path) -> None:
    input_file = tmp_path / "in_silent.mp4"
    output_file = tmp_path / "out_silent.mp4"

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "testsrc=duration=2:size=640x360:rate=25",
        "-c:v", "libx264",
        str(input_file)
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    assert await check_audio_stream(input_file) is False

    duration = await convert_to_video_note(input_file, output_file, resolution=480, max_duration_seconds=10)
    assert duration <= 10

    meta = probe_file(output_file)
    v_stream = next(s for s in meta["streams"] if s["codec_type"] == "video")
    a_stream = next((s for s in meta["streams"] if s["codec_type"] == "audio"), None)

    assert v_stream["width"] == 480 and v_stream["height"] == 480
    assert v_stream["pix_fmt"] == "yuv420p"
    assert a_stream is not None
    assert a_stream["codec_name"] == "aac"
