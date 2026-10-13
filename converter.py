import asyncio
from pathlib import Path


class ConversionError(Exception):
    pass


async def check_audio_stream(source_path: Path) -> bool:
    probe_process = await asyncio.create_subprocess_exec(
        "ffprobe",
        "-v", "error",
        "-select_streams", "a:0",
        "-show_entries", "stream=codec_type",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(source_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout_bytes, _ = await probe_process.communicate()
    return "audio" in stdout_bytes.decode(errors="ignore").lower()


async def get_video_duration(media_path: Path, max_duration_seconds: int = 60) -> int:
    probe_process = await asyncio.create_subprocess_exec(
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(media_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout_bytes, _ = await probe_process.communicate()
    raw_duration = stdout_bytes.decode(errors="ignore").strip()
    try:
        parsed_seconds = float(raw_duration)
        return min(max(1, int(round(parsed_seconds))), max_duration_seconds)
    except (ValueError, TypeError):
        return 1


async def convert_to_video_note(
    source_path: Path,
    target_path: Path,
    resolution: int = 480,
    max_duration_seconds: int = 60,
) -> int:
    has_audio = await check_audio_stream(source_path)
    video_filter = f"crop='min(iw,ih)':'min(iw,ih)',scale={resolution}:{resolution}"
    time_limit = f"{max_duration_seconds - 0.1:.1f}"

    if has_audio:
        ffmpeg_arguments = [
            "ffmpeg", "-y",
            "-i", str(source_path),
            "-t", time_limit,
            "-vf", video_filter,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "20",
            "-profile:v", "main",
            "-level", "3.1",
            "-pix_fmt", "yuv420p",
            "-r", "30",
            "-c:a", "aac",
            "-b:a", "128k",
            "-ar", "44100",
            "-ac", "2",
            "-movflags", "+faststart",
            str(target_path),
        ]
    else:
        ffmpeg_arguments = [
            "ffmpeg", "-y",
            "-i", str(source_path),
            "-f", "lavfi",
            "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
            "-t", time_limit,
            "-vf", video_filter,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "20",
            "-profile:v", "main",
            "-level", "3.1",
            "-pix_fmt", "yuv420p",
            "-r", "30",
            "-c:a", "aac",
            "-b:a", "64k",
            "-shortest",
            "-movflags", "+faststart",
            str(target_path),
        ]

    conversion_process = await asyncio.create_subprocess_exec(
        *ffmpeg_arguments,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr_bytes = await conversion_process.communicate()

    if conversion_process.returncode != 0:
        error_details = stderr_bytes.decode(errors="ignore")
        raise ConversionError(f"FFmpeg process exited with code {conversion_process.returncode}: {error_details[-300:]}")

    return await get_video_duration(target_path, max_duration_seconds)
