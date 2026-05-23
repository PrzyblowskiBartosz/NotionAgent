import os
import re
from datetime import datetime


def _slug(title: str) -> str:
    slug = title.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    return slug[:60] or "notion-page"


def _block_to_md(block: dict) -> str:
    btype = block.get("block_type", "unknown")
    text = block.get("plain_text") or ""
    indent = "  " * block.get("indent_level", 0)
    checked = block.get("checked")

    match btype:
        case "heading_1":
            return f"# {text}"
        case "heading_2":
            return f"## {text}"
        case "heading_3":
            return f"### {text}"
        case "bulleted":
            return f"{indent}- {text}"
        case "numbered":
            return f"{indent}1. {text}"
        case "todo":
            box = "[x]" if checked else "[ ]"
            return f"{indent}- {box} {text}"
        case "divider":
            return "---"
        case "quote":
            return f"> {text}"
        case "code":
            return f"```\n{text}\n```"
        case "paragraph":
            return text
        case _:
            return f"<!-- {btype} --> {text}" if text else f"<!-- {btype} -->"


def export(title: str, blocks: list[dict], output_dir: str) -> str:
    os.makedirs(output_dir, exist_ok=True)
    slug = _slug(title)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    lines = [f"# {title}", ""]
    for block in blocks:
        lines.append(_block_to_md(block))
    lines.append("")
    content = "\n".join(lines)

    timestamped_path = os.path.join(output_dir, f"{slug}_{timestamp}.md")
    latest_path = os.path.join(output_dir, f"{slug}_latest.md")

    with open(timestamped_path, "w", encoding="utf-8") as f:
        f.write(content)
    with open(latest_path, "w", encoding="utf-8") as f:
        f.write(content)

    return timestamped_path
