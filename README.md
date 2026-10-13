<h1 align="center">VideoToCircle</h1>

<p align="center">
  <b>Telegram bot for converting video files and GIFs into circular video notes.</b>
</p>

<p align="center">
  <a href="README_RU.md">Документация на русском языке</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-blue?style=flat-square" alt="Python">
  <img src="https://img.shields.io/badge/docker-ready-2496ED?style=flat-square" alt="Docker">
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License">
</p>

---

Converts inbound videos (MP4, MOV, WEBM, MKV, AVI, FLV) and animated GIFs into square 1:1 round video notes sent via Telegram Bot API (`sendVideoNote`). For silent videos and GIFs, a silent AAC audio track is synthesized automatically to prevent mobile playback freeze on iOS and Android.

## Quick Start

### 1. Docker Deployment (Recommended)

System dependencies and FFmpeg are bundled in the container image.

```bash
cp .env.example .env
# Set BOT_TOKEN in .env
docker compose up -d --build
```

View application logs:
```bash
docker compose logs -f
```

### 2. Up to 2 GB File Support (Local Bot API)

The official Telegram cloud Bot API limits downloads to 20 MB. To process larger video files up to 2 GB, run a local Telegram Bot API server:

1. Obtain `api_id` and `api_hash` from [my.telegram.org](https://my.telegram.org).
2. Configure `.env`:
   ```ini
   MAX_FILE_SIZE_MB=2000
   LOCAL_BOT_API_URL=http://telegram-bot-api:8081
   TELEGRAM_API_ID=your_api_id
   TELEGRAM_API_HASH=your_api_hash
   ```
3. Start services with the `local-api` profile:
   ```bash
   docker compose --profile local-api up -d --build
   ```

### 3. Direct Host Installation

Requires Python 3.10+ and FFmpeg with ffprobe in system `PATH`.

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
Install Python 3.10+, download FFmpeg and add the `bin` directory to your system `PATH`.
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python bot.py
```

## Configuration

Settings are managed via `.env` or system environment variables:

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `BOT_TOKEN` | string | (required) | Telegram bot token from @BotFather |
| `MAX_FILE_SIZE_MB` | int | `1000` | Maximum allowed inbound file size in MB |
| `MAX_CONCURRENT_TASKS` | int | `3` | Maximum concurrent FFmpeg encoding jobs |
| `TARGET_RESOLUTION` | int | `480` | Output square dimension in pixels (480x480) |
| `MAX_DURATION_SECONDS` | int | `60` | Maximum duration limit for round notes |
| `LOCAL_BOT_API_URL` | string | `None` | Local Bot API endpoint URL for files up to 2 GB |
| `TEMP_DIR` | string | `temp` | Directory for temporary conversion files |

## Commands and Localization

- `/start`: Prompts the user to select their language (English or Russian, text buttons without flag symbols) only on the very first start. Subsequent invocations immediately display the guide in the saved language. Default language is English.
- `/language` (or `/lang`): Switch interface language at any time.
- `/help`: Display format requirements and operational limits.

## Technical Details

- **Aspect Ratio**: Centered crop `crop='min(iw,ih)':'min(iw,ih)',scale=480:480`.
- **Video Stream**: H.264 Main Profile, Level 3.1, `yuv420p` pixel format, constant 30 fps.
- **Audio Stream**: AAC-LC 128 kbps. For silent videos or GIFs, the `anullsrc` filter synthesizes a silent track.
- **Faststart**: The `-movflags +faststart` flag places the moov atom at the beginning of the container for immediate streaming.
- **Concurrency**: FFmpeg executions are queued through an `asyncio.Semaphore` to protect CPU from exhaustion.

## Known Limitations

- **File Size**: Up to 20 MB when using standard Telegram cloud servers; up to 2000 MB when running a local Telegram Bot API server.
- **Duration**: Telegram limits video notes to 60 seconds (longer media is hard-trimmed automatically).

## License

MIT License. See [LICENSE](LICENSE) for details.
