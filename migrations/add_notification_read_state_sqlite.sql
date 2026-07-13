-- Shared notification read markers for local SQLite mode.
CREATE TABLE IF NOT EXISTS notification_read_state (
    scope TEXT NOT NULL,
    notification_id TEXT NOT NULL,
    read_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (scope, notification_id)
);
