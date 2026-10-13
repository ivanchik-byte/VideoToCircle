<h1 align="center">VideoToCircle</h1>

<p align="center">
  <b>Telegram-бот для конвертации видео любых форматов и GIF в круглые видеосообщения (кружочки).</b>
</p>

<p align="center">
  <a href="README.md">English documentation</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-blue?style=flat-square" alt="Python">
  <img src="https://img.shields.io/badge/docker-ready-2496ED?style=flat-square" alt="Docker">
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License">
</p>

---

Бот принимает видеозаписи (MP4, MOV, WEBM, MKV, AVI, FLV) и GIF-анимации, центрирует кадр в квадрат 1:1, кодирует в H.264/AAC и отправляет через Telegram Bot API (`sendVideoNote`). Для беззвучных роликов и GIF генерируется тихая аудиодорожка, предотвращающая зависание мобильных плееров на iOS и Android.

## Быстрый старт

### 1. Стандартный запуск в Docker (файлы до 20 МБ)

Использует стандартный облачный сервер Telegram.

```bash
cp .env.example .env
# укажите BOT_TOKEN в файле .env
docker compose up -d --build
```

### 2. Запуск со снятием лимита до 2 ГБ (Local Bot API)

Облачный сервер Telegram ограничивает скачивание файлов до 20 МБ. Для работы с большими видео (до 2 ГБ) запускается локальный сервер Telegram Bot API:

1. Получите `api_id` и `api_hash` на [my.telegram.org](https://my.telegram.org).
2. Раскомментируйте переменные в `.env`:
   ```ini
   MAX_FILE_SIZE_MB=2000
   LOCAL_BOT_API_URL=http://telegram-bot-api:8081
   TELEGRAM_API_ID=ваш_api_id
   TELEGRAM_API_HASH=ваш_api_hash
   ```
3. Запустите контейнеры с профилем `local-api`:
   ```bash
   docker compose --profile local-api up -d --build
   ```

### 3. Запуск без Docker на любой ОС

Требования: Python 3.10+ и FFmpeg в системном PATH.

**Ubuntu / Debian:**
```bash
sudo apt update && sudo apt install -y ffmpeg python3-venv
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env && python bot.py
```

**macOS:**
```bash
brew install ffmpeg
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env && python bot.py
```

**Windows:**
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python bot.py
```

## Конфигурация

Параметры задаются в файле `.env` или переменных окружения:

| Переменная | Тип | По умолчанию | Описание |
| :--- | :--- | :--- | :--- |
| `BOT_TOKEN` | string | (обязательно) | Токен бота от @BotFather |
| `MAX_FILE_SIZE_MB` | int | `1000` | Максимальный размер входящего файла в МБ |
| `MAX_CONCURRENT_TASKS` | int | `3` | Максимум параллельных кодирований FFmpeg |
| `TARGET_RESOLUTION` | int | `480` | Размер стороны квадратного кадра (480x480) |
| `MAX_DURATION_SECONDS` | int | `60` | Максимальная длительность кружочка |
| `LOCAL_BOT_API_URL` | string | `None` | URL локального Bot API сервера для файлов до 2 ГБ |
| `TEMP_DIR` | string | `temp` | Каталог для временных файлов |

## Команды и локализация

- `/start`: При самом первом запуске предлагает выбрать язык (English или Русский, без флагов). При последующих запусках сразу выводит инструкцию на сохраненном языке. По умолчанию используется английский язык.
- `/language` (или `/lang`): Смена языка интерфейса в любой момент.
- `/help`: Справка по возможностям и поддерживаемым форматам.

## Технические детали

- **Геометрия**: центрированный кроп `crop='min(iw,ih)':'min(iw,ih)',scale=480:480`.
- **Видеокодек**: H.264 Main Profile, уровень 3.1, `yuv420p`, постоянные 30 fps.
- **Аудиокодек**: AAC-LC 128 kbps. Если звук отсутствует (GIF, немой ролик), фильтр `anullsrc` генерирует тишину.
- **Стриминг**: метаданные `-movflags +faststart` обеспечивают запуск воспроизведения до полной загрузки файла.
- **Параллелизм**: конвертация управляется `asyncio.Semaphore`, исключая перегрузку CPU.

## Ограничения

- **Размер файлов**: до 20 МБ на стандартном облачном API Telegram; до 2000 МБ при использовании локального сервера Bot API.
- **Длительность**: до 60 секунд по спецификации Telegram (ролики длиннее 60 секунд обрезаются автоматически).

## Лицензия

MIT. Полный текст доступен в файле [LICENSE](LICENSE).
