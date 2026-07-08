CREATE TABLE IF NOT EXISTS users (
    user_id     INTEGER PRIMARY KEY,
    username    TEXT,
    tos_accepted_at TIMESTAMP,
    tier        TEXT NOT NULL DEFAULT 'free',
    tier_expires_at TIMESTAMP,
    credits     INTEGER NOT NULL DEFAULT 0,
    banned_at   TIMESTAMP,
    last_daily_refresh DATE,
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS generations (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(user_id),
    prompt      TEXT NOT NULL,
    backend     TEXT NOT NULL,
    status      TEXT NOT NULL,
    image_url   TEXT,
    credits_cost INTEGER NOT NULL DEFAULT 0,
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transactions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(user_id),
    delta       INTEGER NOT NULL,
    reason      TEXT NOT NULL,
    telegram_payment_charge_id TEXT,
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS rate_limit_log (
    user_id     INTEGER NOT NULL,
    window_start INTEGER NOT NULL,
    count       INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, window_start)
);

CREATE INDEX IF NOT EXISTS idx_generations_user ON generations(user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_user ON transactions(user_id);
