-- Migration: create_statement_log.sql
-- Creates statement_log table to store parsed statement headers, details and generated MT940 filenames

CREATE TABLE IF NOT EXISTS statement_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    company_id INTEGER REFERENCES company(id) ON DELETE CASCADE,
    bank_code VARCHAR,
    filename VARCHAR NOT NULL,
    original_filename VARCHAR,
    status VARCHAR NOT NULL,
    message TEXT,

    accountno VARCHAR,
    currency VARCHAR,
    opening_balance VARCHAR,
    closing_balance VARCHAR,

    details JSONB,
    mt940_filename VARCHAR,

    processed_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_statement_log_company_id ON statement_log(company_id);
CREATE INDEX IF NOT EXISTS idx_statement_log_user_id ON statement_log(user_id);
CREATE INDEX IF NOT EXISTS idx_statement_log_bank_code ON statement_log(bank_code);
