import hashlib

_TYPE_MAP = {
    "header": "heading_1",
    "sub_header": "heading_2",
    "sub_sub_header": "heading_3",
    "text": "paragraph",
    "bulleted_list": "bulleted",
    "numbered_list": "numbered",
    "to_do": "todo",
    "divider": "divider",
    "quote": "quote",
    "code": "code",
    "callout": "callout",
    "image": "image",
    "bookmark": "bookmark",
    "toggle": "toggle",
}


def clean_blocks(raw: list[dict]) -> list[dict]:
    cleaned = []
    for block in raw:
        text = (block.get("plain_text") or "").strip()
        block_type = block.get("block_type", "unknown")
        normalized = _TYPE_MAP.get(block_type, block_type)

        if normalized == "divider":
            cleaned.append({**block, "block_type": normalized, "plain_text": ""})
            continue

        if not text and normalized not in ("image", "bookmark"):
            continue

        cleaned.append({**block, "block_type": normalized, "plain_text": text})
    return cleaned


def compute_hash(blocks: list[dict]) -> str:
    content = "\n".join(b.get("plain_text") or "" for b in blocks)
    return hashlib.sha256(content.encode()).hexdigest()
