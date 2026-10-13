from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_token: str = ""
    max_concurrent_tasks: int = 3
    target_resolution: int = 480
    max_duration_seconds: int = 60
    max_file_size_mb: int = 1000
    local_bot_api_url: str | None = None
    local_bot_api_is_local: bool = False
    temp_dir: Path = Path("temp")
    data_dir: Path = Path("data")

    def ensure_temp_dir(self) -> Path:
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        return self.temp_dir

    def ensure_data_dir(self) -> Path:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        return self.data_dir


settings = Settings()
