
-- Stock Trading System - Schema v0.8 (PostgreSQL)
-- Generated for Phase 2 implementation
-- Safe to run multiple times if you drop existing tables first (optional)

-- Optional: create schema namespace
CREATE SCHEMA IF NOT EXISTS trading;
SET search_path TO trading, public;

-- Drop order for clean rebuild (optional). Comment these out in production.
-- DROP TABLE IF EXISTS transactions CASCADE;
-- DROP TABLE IF EXISTS orders CASCADE;
-- DROP TABLE IF EXISTS cash_accounts CASCADE;
-- DROP TABLE IF EXISTS stocks CASCADE;
-- DROP TABLE IF EXISTS market_holidays CASCADE;
-- DROP TABLE IF EXISTS market_hours CASCADE;
-- DROP TABLE IF EXISTS users CASCADE;

-- 1) users
CREATE TABLE IF NOT EXISTS users (
    id              BIGSERIAL PRIMARY KEY,
    full_name       VARCHAR(120)        NOT NULL,
    username        VARCHAR(50)         NOT NULL UNIQUE,
    email           VARCHAR(120)        NOT NULL UNIQUE,
    role            VARCHAR(20)         NOT NULL CHECK (role IN ('customer','admin')),
    password_hash   TEXT                NOT NULL,
    created_at      TIMESTAMP           NOT NULL DEFAULT NOW()
);

-- 2) cash_accounts (1:1 with users)
CREATE TABLE IF NOT EXISTS cash_accounts (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT              NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    balance_cents   BIGINT              NOT NULL DEFAULT 0,
    updated_at      TIMESTAMP           NOT NULL DEFAULT NOW()
);

-- 3) stocks
CREATE TABLE IF NOT EXISTS stocks (
    id              BIGSERIAL PRIMARY KEY,
    ticker          VARCHAR(10)         NOT NULL UNIQUE,
    company_name    VARCHAR(160)        NOT NULL,
    volume          BIGINT              NOT NULL CHECK (volume >= 0),
    current_price_cents  BIGINT         NOT NULL CHECK (current_price_cents >= 0),
    opening_price_cents  BIGINT         NOT NULL CHECK (opening_price_cents >= 0),
    daily_high_cents     BIGINT         NOT NULL DEFAULT 0 CHECK (daily_high_cents >= 0),
    daily_low_cents      BIGINT         NOT NULL DEFAULT 0 CHECK (daily_low_cents >= 0),
    updated_at      TIMESTAMP           NOT NULL DEFAULT NOW()
);

-- 4) orders (each order for one stock, by one user)
CREATE TABLE IF NOT EXISTS orders (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT              NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    stock_id        BIGINT              NOT NULL REFERENCES stocks(id) ON DELETE RESTRICT,
    order_type      VARCHAR(10)         NOT NULL CHECK (order_type IN ('buy','sell')),
    shares          BIGINT              NOT NULL CHECK (shares > 0),
    status          VARCHAR(15)         NOT NULL CHECK (status IN ('pending','executed','canceled')),
    created_at      TIMESTAMP           NOT NULL DEFAULT NOW(),
    executed_at     TIMESTAMP           NULL
);

CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_stock ON orders(stock_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);

-- 5) transactions (immutable audit of financial events)
CREATE TABLE IF NOT EXISTS transactions (
    id              BIGSERIAL PRIMARY KEY,
    order_id        BIGINT              NULL REFERENCES orders(id) ON DELETE SET NULL,
    user_id         BIGINT              NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    stock_id        BIGINT              NULL REFERENCES stocks(id) ON DELETE SET NULL,
    transaction_type VARCHAR(20)        NOT NULL CHECK (transaction_type IN ('buy','sell','deposit','withdrawal','canceled')),
    amount_cents    BIGINT              NOT NULL CHECK (amount_cents >= 0),
    shares          BIGINT              NULL CHECK (shares IS NULL OR shares >= 0),
    created_at      TIMESTAMP           NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tx_user ON transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_tx_order ON transactions(order_id);
CREATE INDEX IF NOT EXISTS idx_tx_type  ON transactions(transaction_type);

-- 6) market_hours (single-row table in most cases)
CREATE TABLE IF NOT EXISTS market_hours (
    id              SMALLSERIAL PRIMARY KEY,
    opens_at        TIME NOT NULL,
    closes_at       TIME NOT NULL,
    CHECK (opens_at < closes_at)
);

-- 7) market_holidays
CREATE TABLE IF NOT EXISTS market_holidays (
    id              BIGSERIAL PRIMARY KEY,
    holiday_date    DATE NOT NULL UNIQUE,
    description     VARCHAR(200)
);

-- Helpful computed view: portfolio positions per user
CREATE OR REPLACE VIEW v_user_positions AS
SELECT
    o.user_id,
    s.ticker,
    COALESCE(SUM(CASE WHEN t.transaction_type='buy' THEN t.shares WHEN t.transaction_type='sell' THEN -t.shares ELSE 0 END),0) AS shares_held
FROM orders o
JOIN stocks s ON s.id = o.stock_id
LEFT JOIN transactions t ON t.order_id = o.id
GROUP BY o.user_id, s.ticker;

-- Helpful computed view: cash balance in dollars
CREATE OR REPLACE VIEW v_cash_balances AS
SELECT u.id AS user_id,
       (ca.balance_cents::numeric / 100.0) AS balance_dollars
FROM users u
JOIN cash_accounts ca ON ca.user_id = u.id;
