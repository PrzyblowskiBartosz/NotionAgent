import logging
import re
from collections import deque

from playwright.sync_api import sync_playwright, Page as PlaywrightPage

from app.config import settings

logger = logging.getLogger(__name__)

_CONTENT_SELECTOR = "[data-block-id]"
_MAX_SCROLL_ATTEMPTS = 30
_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def _scroll_to_load_all(page: PlaywrightPage) -> None:
    prev_height = -1
    attempts = 0
    while attempts < _MAX_SCROLL_ATTEMPTS:
        page.evaluate("window.scrollBy(0, 600)")
        page.wait_for_timeout(500)
        height = page.evaluate("document.body.scrollHeight")
        if height == prev_height:
            break
        prev_height = height
        attempts += 1


def _extract_title(page: PlaywrightPage) -> str:
    title = page.title()
    return title.replace(" – Notion", "").replace(" | Notion", "").strip() or "Untitled"


def _extract_blocks(page: PlaywrightPage) -> list[dict]:
    return page.evaluate("""
        () => {
            function inferType(el) {
                const cls = el.className || '';
                if (cls.includes('header')) return 'header';
                if (cls.includes('sub_header')) return 'sub_header';
                if (cls.includes('bulleted')) return 'bulleted_list';
                if (cls.includes('numbered')) return 'numbered_list';
                if (cls.includes('to_do')) return 'to_do';
                if (cls.includes('divider')) return 'divider';
                if (cls.includes('quote')) return 'quote';
                if (cls.includes('code')) return 'code';
                return 'text';
            }
            const elements = document.querySelectorAll('[data-block-id]');
            const results = [];
            elements.forEach((el, index) => {
                const blockType = el.getAttribute('data-block-type') || inferType(el);
                const plainText = el.innerText ? el.innerText.trim() : '';
                const checked = el.getAttribute('aria-checked');
                const paddingLeft = parseFloat(window.getComputedStyle(el).paddingLeft) || 0;
                results.push({
                    block_type: blockType,
                    plain_text: plainText,
                    checked: checked === 'true' ? true : (checked === 'false' ? false : null),
                    indent_level: Math.round(paddingLeft / 24),
                    position: index,
                });
            });
            return results;
        }
    """)


def _extract_subpage_links(page: PlaywrightPage, current_url: str) -> list[str]:
    links = page.evaluate("""
        () => {
            const pattern = /https:\\/\\/www\\.notion\\.so\\/[^/]*[a-f0-9]{32}$/;
            const seen = new Set();
            const results = [];
            document.querySelectorAll('a[href]').forEach(a => {
                const cleanHref = a.href.split('?')[0].split('#')[0];
                if (pattern.test(cleanHref) && !seen.has(cleanHref)) {
                    seen.add(cleanHref);
                    results.push(cleanHref);
                }
            });
            return results;
        }
    """)
    current_clean = current_url.split("?")[0].split("#")[0].rstrip("/")
    return [url for url in links if url.rstrip("/") != current_clean]


def _scrape_one(page: PlaywrightPage, url: str) -> tuple[str, list[dict]]:
    logger.info("Scraping: %s", url)
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    try:
        page.wait_for_selector(_CONTENT_SELECTOR, timeout=20000)
    except Exception:
        raise RuntimeError(f"Timed out waiting for content at {url}")
    _scroll_to_load_all(page)
    page.wait_for_timeout(2000)
    return _extract_title(page), _extract_blocks(page)


def scrape_pages(root_url: str, max_depth: int) -> list[dict]:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=settings.headless,
            args=[
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--no-sandbox",
                "--no-zygote",
                "--disable-setuid-sandbox",
                "--js-flags=--max-old-space-size=256",
            ],
        )
        context = browser.new_context(user_agent=_UA)
        page = context.new_page()

        results = []
        visited: set[str] = set()
        queue: deque[tuple[str, str | None, int]] = deque()
        queue.append((root_url, None, 0))

        while queue:
            url, parent_url, depth = queue.popleft()
            normalized = url.rstrip("/")
            if normalized in visited:
                continue
            visited.add(normalized)

            try:
                title, blocks = _scrape_one(page, url)
            except Exception as exc:
                logger.warning("Skipping %s — %s", url, exc)
                continue

            subpage_links = []
            if depth < max_depth:
                subpage_links = _extract_subpage_links(page, url)
                for link in subpage_links:
                    if link.rstrip("/") not in visited:
                        queue.append((link, url, depth + 1))

            results.append({
                "url": url,
                "title": title,
                "blocks": blocks,
                "parent_url": parent_url,
                "depth": depth,
            })
            logger.info("Done (%d blocks, %d sublinks) — %s", len(blocks), len(subpage_links), title)

        browser.close()

    logger.info("Scraping complete — %d pages total", len(results))
    return results
