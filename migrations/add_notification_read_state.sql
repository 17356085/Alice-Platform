-- Shared notification read markers for PostgreSQL mode.
CREATE TABLE IF NOT EXISTS notification_read_state (
    scope VARCHAR(200) NOT NULL,
    notification_id VARCHAR(256) NOT NULL,
    read_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (scope, notification_id)
);
