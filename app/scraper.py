import logging
import os

from playwright.sync_api import sync_playwright, Browser, BrowserContext

from app.config import settings

logger = logging.getLogger(__name__)

_CONTENT_SELECTOR = "[data-block-id]"
_MAX_SCROLL_ATTEMPTS = 30
_LOGIN_TIMEOUT_MS = 5 * 60 * 1000  # 5 minutes for magic link round-trip


def _make_context(browser: Browser) -> BrowserContext:
    if os.path.exists(settings.session_file):
        logger.info("Loading saved session from %s", settings.session_file)
        return browser.new_context(
            storage_state=settings.session_file,
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )
    return browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    )


def _handle_login(pw, context_state: dict | None) -> BrowserContext:
    """Open a non-headless browser so the user can complete magic link login."""
    print(
        "\n[NotionAgent] Login required.\n"
        "  A browser window has been opened — please log in to Notion via the\n"
        "  magic link that will be sent to your email.\n"
        "  The script will continue automatically once you are logged in.\n"
    )
    browser = pw.chromium.launch(headless=False)
    kwargs = dict(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    )
    if context_state:
        kwargs["storage_state"] = context_state
    context = browser.new_context(**kwargs)
    page = context.new_page()
    page.goto(settings.notion_page_url, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_url(
        lambda url: "notion.so/login" not in url,
        timeout=_LOGIN_TIMEOUT_MS,
    )
    context.storage_state(path=settings.session_file)
    logger.info("Session saved to %s", settings.session_file)
    return context, browser


def _scroll_to_load_all(page) -> None:
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


def _extract_title(page) -> str:
    title = page.title()
    return title.replace(" – Notion", "").replace(" | Notion", "").strip() or "Untitled"


def _extract_blocks(page) -> list[dict]:
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


def scrape_page() -> tuple[str, list[dict]]:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=settings.headless)
        context = _make_context(browser)
        page = context.new_page()

        logger.info("Navigating to %s", settings.notion_page_url)
        page.goto(settings.notion_page_url, wait_until="domcontentloaded", timeout=30000)

        if "notion.so/login" in page.url:
            browser.close()
            context, browser = _handle_login(pw, None)
            page = context.pages[0] if context.pages else context.new_page()
            page.goto(settings.notion_page_url, wait_until="domcontentloaded", timeout=30000)

        logger.info("Waiting for content to render")
        try:
            page.wait_for_selector(_CONTENT_SELECTOR, timeout=20000)
        except Exception:
            raise RuntimeError(
                "Timed out waiting for Notion content — "
                "page may be private or selectors have changed"
            )

        _scroll_to_load_all(page)
        title = _extract_title(page)
        blocks = _extract_blocks(page)
        browser.close()

    logger.info("Scraped %d blocks from %r", len(blocks), title)
    return title, blocks
