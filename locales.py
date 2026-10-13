from typing import Final

DEFAULT_LANGUAGE: Final[str] = "en"

MESSAGES: Final[dict[str, dict[str, str]]] = {
    "en": {
        "select_language": "Choose your interface language / Выберите язык интерфейса:",
        "btn_english": "English",
        "btn_russian": "Русский",
        "language_saved": "Language set to English.",
        "start": (
            "Send any video, GIF animation, or video document.\n\n"
            "I will center-crop it to a 1:1 square and send you a circular video note.\n"
            "Maximum file size: {max_mb} MB.\n"
            "Maximum duration: 60 seconds."
        ),
        "help": (
            "Usage guide:\n\n"
            "1. Send a video, GIF, or video file (MP4, MOV, WEBM, MKV, AVI).\n"
            "2. The frame is centered, scaled to 1:1, and converted into a round video note.\n"
            "3. Silent videos and GIFs get a generated audio track so mobile players run properly.\n\n"
            "Commands:\n"
            "/start - Restart the bot\n"
            "/language - Change interface language\n"
            "/help - Show this guide"
        ),
        "unsupported_document": "Unsupported document format. Please send a video file or GIF.",
        "file_too_large": "File exceeds the configured limit of {max_mb} MB.",
        "downloading": "Downloading file...",
        "converting": "Converting to video note...",
        "uploading": "Uploading video note...",
        "conversion_error": "Failed to process video. Make sure the file has valid video streams.",
        "unexpected_error": "An unexpected error occurred while processing the file.",
    },
    "ru": {
        "select_language": "Выберите язык интерфейса / Choose your interface language:",
        "btn_english": "English",
        "btn_russian": "Русский",
        "language_saved": "Язык интерфейса изменен на русский.",
        "start": (
            "Отправьте любое видео, GIF-анимацию или видеофайл документом.\n\n"
            "Я обрежу видео по центру в квадрат 1:1 и пришлю видеосообщение в кружочке.\n"
            "Максимальный размер файла: {max_mb} МБ.\n"
            "Максимальная длительность: 60 секунд."
        ),
        "help": (
            "Инструкция по использованию:\n\n"
            "1. Отправьте видеозапись, анимацию GIF или файл формата MP4, MOV, WEBM, MKV, AVI.\n"
            "2. Бот автоматически центрирует кадр, сжимает его в пропорции 1:1 и формирует кружочек.\n"
            "3. Для роликов без звука и GIF автоматически синтезируется тихая аудиодорожка для корректного воспроизведения на смартфонах.\n\n"
            "Команды:\n"
            "/start - Перезапуск бота\n"
            "/language - Смена языка интерфейса\n"
            "/help - Справка"
        ),
        "unsupported_document": "Неподдерживаемый формат документа. Отправьте видеофайл или GIF.",
        "file_too_large": "Файл превышает установленный лимит в {max_mb} МБ.",
        "downloading": "Скачивание файла...",
        "converting": "Конвертация в видеокружочек...",
        "uploading": "Отправка видеосообщения...",
        "conversion_error": "Ошибка при обработке видео. Убедитесь, что файл содержит корректные видеоданные.",
        "unexpected_error": "Произошла непредвиденная ошибка при обработке файла.",
    },
}


def t(key: str, lang: str | None = None, **kwargs: object) -> str:
    chosen_lang = lang if lang in MESSAGES else DEFAULT_LANGUAGE
    template = MESSAGES[chosen_lang].get(key, MESSAGES[DEFAULT_LANGUAGE].get(key, key))
    if kwargs:
        return template.format(**kwargs)
    return template
