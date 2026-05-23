import logging

from sqlalchemy import delete

from app.config import settings
from app.database import get_session
from app.models import Block, ChangeLogEntry, Page
from app.scraper import scrape_page
from app.parser import clean_blocks, compute_hash
from app import md_exporter

logger = logging.getLogger(__name__)


def run() -> None:
    try:
        _sync()
    except Exception as exc:
        logger.error("Sync failed: %s", exc, exc_info=True)
        raise


def _sync() -> None:
    title, raw_blocks = scrape_page()
    blocks = clean_blocks(raw_blocks)
    new_hash = compute_hash(blocks)

    with get_session() as session:
        page = session.query(Page).filter_by(notion_url=settings.notion_page_url).first()

        if page is None:
            page = Page(
                notion_url=settings.notion_page_url,
                title=title,
                content_hash=new_hash,
            )
            session.add(page)
            session.flush()
            _insert_blocks(session, page.id, blocks)
            session.add(ChangeLogEntry(
                page_id=page.id,
                change_type="created",
                new_hash=new_hash,
                detail=f"First sync — {len(blocks)} blocks captured",
            ))
            path = md_exporter.export(title, blocks, settings.output_dir)
            logger.info("Created — %d blocks saved. MD: %s", len(blocks), path)

        elif page.content_hash != new_hash:
            old_hash = page.content_hash
            page.title = title
            page.content_hash = new_hash
            session.execute(delete(Block).where(Block.page_id == page.id))
            _insert_blocks(session, page.id, blocks)
            session.add(ChangeLogEntry(
                page_id=page.id,
                change_type="updated",
                old_hash=old_hash,
                new_hash=new_hash,
                detail=f"Content changed — {len(blocks)} blocks",
            ))
            path = md_exporter.export(title, blocks, settings.output_dir)
            logger.info("Updated — %d blocks saved. MD: %s", len(blocks), path)

        else:
            logger.info("No changes detected (hash: %s…)", new_hash[:12])


def _insert_blocks(session, page_id: int, blocks: list[dict]) -> None:
    for block in blocks:
        session.add(Block(
            page_id=page_id,
            block_type=block["block_type"],
            plain_text=block.get("plain_text"),
            checked=block.get("checked"),
            indent_level=block.get("indent_level", 0),
            position=block.get("position", 0),
        ))
