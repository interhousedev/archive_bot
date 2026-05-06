from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # MongoDB
    mongo_uri: str
    mongo_db_name: str

    # Telegram Bot API
    botapi_token: str | None = None
    botapi_server_url: str | None = None  # local Bot API server, e.g. http://telegram-bot-api:8081
    # Path where local Bot API server stores files. On the host (dev) set to ./data/botapi.
    # In Docker (prod) keep as /var/lib/telegram-bot-api (same as the mounted bind mount).
    botapi_local_files_path: str = "/var/lib/telegram-bot-api"
    botapi_data_dir: str = "/var/lib/telegram-bot-api"  # data dir used by local Bot API server
    admins_ids: list[int] = []

    # EMIS
    emis_base_url: str = "https://emis.edu.uz/api/v1/"
    emis_institution_id: int = 0

    # S3 (Cloupard or any S3-compatible)
    s3_endpoint_url: str
    s3_access_key: str
    s3_secret_key: str
    s3_bucket_name: str
    s3_base_url: str

    # Web (FastAPI)
    webapp_base_url: str | None = None
    web_host: str = "0.0.0.0"
    web_port: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
