import logging

from app.config import settings
from app.database import init_db
from app.sync import run

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

if __name__ == "__main__":
    init_db()
    run()
