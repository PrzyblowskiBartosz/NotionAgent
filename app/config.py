import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv(os.getenv("ENV_FILE", ".env"))


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Required environment variable {name!r} is not set")
    return value


def _require_unless_database_url(name: str) -> str:
    if os.getenv("DATABASE_URL"):
        return os.getenv(name, "")
    return _require(name)


@dataclass
class Settings:
    notion_page_url: str
    postgres_host: str
    postgres_port: int
    postgres_db: str
    postgres_user: str
    postgres_password: str
    database_url: str | None
    log_level: str
    headless: bool
    output_dir: str
    max_depth: int
    debug: bool


settings = Settings(
    notion_page_url=_require("NOTION_PAGE_URL"),
    postgres_host=_require_unless_database_url("POSTGRES_HOST"),
    postgres_port=int(os.getenv("POSTGRES_PORT", "5432")),
    postgres_db=_require_unless_database_url("POSTGRES_DB"),
    postgres_user=_require_unless_database_url("POSTGRES_USER"),
    postgres_password=_require_unless_database_url("POSTGRES_PASSWORD"),
    database_url=os.getenv("DATABASE_URL"),
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    headless=os.getenv("HEADLESS", "true").lower() == "true",
    output_dir=os.getenv("OUTPUT_DIR", "output"),
    max_depth=int(os.getenv("MAX_DEPTH", "2")),
    debug=os.getenv("DEBUG", "false").lower() == "true",
)
