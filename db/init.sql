CREATE TABLE IF NOT EXISTS pages (
    id           BIGSERIAL PRIMARY KEY,
    notion_url   TEXT NOT NULL UNIQUE,
    title        TEXT,
    content_hash TEXT,
    parent_id    BIGINT REFERENCES pages(id),
    depth        INTEGER NOT NULL DEFAULT 0,
    synced_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS blocks (
    id              BIGSERIAL PRIMARY KEY,
    page_id         BIGINT NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
    block_type      TEXT NOT NULL,
    plain_text      TEXT,
    checked         BOOLEAN,
    indent_level    INTEGER NOT NULL DEFAULT 0,
    position        INTEGER NOT NULL DEFAULT 0,
    synced_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_blocks_page_id ON blocks(page_id);

CREATE TABLE IF NOT EXISTS change_log (
    id          BIGSERIAL PRIMARY KEY,
    event_time  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    page_id     BIGINT NOT NULL REFERENCES pages(id),
    change_type TEXT NOT NULL,
    old_hash    TEXT,
    new_hash    TEXT,
    detail      TEXT
);

CREATE INDEX IF NOT EXISTS idx_change_log_event_time ON change_log(event_time);
