import logging

from sqlalchemy import delete

from app.config import settings
from app.database import get_session
from app.models import Block, ChangeLogEntry, Page
from app.scraper import scrape_pages
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
    pages = scrape_pages(settings.notion_page_url, settings.max_depth)

    url_to_id: dict[str, int] = {}
    new_count = updated_count = unchanged_count = 0

    with get_session() as session:
        for page_data in pages:
            url = page_data["url"]
            title = page_data["title"]
            blocks = clean_blocks(page_data["blocks"])
            new_hash = compute_hash(blocks)
            parent_id = url_to_id.get(page_data["parent_url"]) if page_data["parent_url"] else None
            depth = page_data["depth"]

            page = session.query(Page).filter_by(notion_url=url).first()

            if page is None:
                page = Page(
                    notion_url=url,
                    title=title,
                    content_hash=new_hash,
                    parent_id=parent_id,
                    depth=depth,
                )
                session.add(page)
                session.flush()
                _insert_blocks(session, page.id, blocks)
                session.add(ChangeLogEntry(
                    page_id=page.id,
                    change_type="created",
                    new_hash=new_hash,
                    detail=f"First sync — {len(blocks)} blocks",
                ))
                md_exporter.export(title, blocks, settings.output_dir)
                new_count += 1

            elif page.content_hash != new_hash:
                old_hash = page.content_hash
                page.title = title
                page.content_hash = new_hash
                page.parent_id = parent_id
                page.depth = depth
                session.execute(delete(Block).where(Block.page_id == page.id))
                _insert_blocks(session, page.id, blocks)
                session.add(ChangeLogEntry(
                    page_id=page.id,
                    change_type="updated",
                    old_hash=old_hash,
                    new_hash=new_hash,
                    detail=f"Content changed — {len(blocks)} blocks",
                ))
                md_exporter.export(title, blocks, settings.output_dir)
                updated_count += 1

            else:
                unchanged_count += 1

            url_to_id[url] = page.id

    logger.info(
        "Sync complete. Pages: %d | New: %d Updated: %d Unchanged: %d",
        len(pages), new_count, updated_count, unchanged_count,
    )


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
