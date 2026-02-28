
-- Seed data for local development/testing
SET search_path TO trading, public;

INSERT INTO users (full_name, username, email, role, password_hash)
VALUES
('Test Customer','customer1','customer1@example.com','customer','$2b$12$dummyhash'),
('Admin User','admin1','admin1@example.com','admin','$2b$12$dummyhash')
ON CONFLICT (username) DO NOTHING;

-- Give customer a cash account with $10,000.00
INSERT INTO cash_accounts (user_id, balance_cents)
SELECT id, 1000000 FROM users WHERE username='customer1'
ON CONFLICT (user_id) DO NOTHING;

-- Sample stocks
INSERT INTO stocks (ticker, company_name, volume, current_price_cents, opening_price_cents, daily_high_cents, daily_low_cents)
VALUES
('AAPL','Apple Inc.', 1000000000, 18000, 17800, 18200, 17600),
('TSLA','Tesla, Inc.', 800000000, 24000, 23500, 24300, 23000)
ON CONFLICT (ticker) DO NOTHING;

-- Market hours 9:30 to 16:00 (example)
INSERT INTO market_hours (opens_at, closes_at)
VALUES ('09:30','16:00')
ON CONFLICT DO NOTHING;
