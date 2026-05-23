import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Required environment variable {name!r} is not set")
    return value


@dataclass
class Settings:
    notion_page_url: str
    postgres_host: str
    postgres_port: int
    postgres_db: str
    postgres_user: str
    postgres_password: str
    log_level: str
    headless: bool
    output_dir: str
    session_file: str
    max_depth: int


settings = Settings(
    notion_page_url=_require("NOTION_PAGE_URL"),
    postgres_host=_require("POSTGRES_HOST"),
    postgres_port=int(os.getenv("POSTGRES_PORT", "5432")),
    postgres_db=_require("POSTGRES_DB"),
    postgres_user=_require("POSTGRES_USER"),
    postgres_password=_require("POSTGRES_PASSWORD"),
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    headless=os.getenv("HEADLESS", "true").lower() == "true",
    output_dir=os.getenv("OUTPUT_DIR", "output"),
    session_file=os.getenv("SESSION_FILE", "session.json"),
    max_depth=int(os.getenv("MAX_DEPTH", "2")),
)
