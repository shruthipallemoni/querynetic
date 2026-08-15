-- Test schema + sample data for local Querynetic testing.
-- Run with:
--   docker exec -i querynetic-test-db psql -U postgres -d test_db < backend/scripts/seed_data.sql
--
-- IDEMPOTENT: safe to run this any number of times. The TRUNCATE below
-- clears both tables first, so re-running never duplicates rows — running
-- an insert-only script twice by accident is exactly what caused revenue
-- totals to come out exactly double earlier.

CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    signup_date DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id),
    amount NUMERIC(10, 2) NOT NULL,
    region TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

-- Clears both tables (and resets auto-increment ids) before every insert,
-- regardless of how many times this script has already been run.
TRUNCATE TABLE orders, customers RESTART IDENTITY CASCADE;

INSERT INTO customers (name, signup_date) VALUES
    ('Alice Chen', '2024-01-15'),
    ('Marcus Reyes', '2024-02-20'),
    ('Priya Nair', '2024-03-05');

INSERT INTO orders (customer_id, amount, region, created_at) VALUES
    (1, 120.50, 'Europe', '2024-06-01'),
    (1, 89.99,  'Europe', '2024-06-15'),
    (2, 250.00, 'North America', '2024-06-03'),
    (2, 175.25, 'North America', '2024-06-20'),
    (3, 310.75, 'North America', '2024-06-10');