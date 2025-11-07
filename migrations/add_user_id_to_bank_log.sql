-- Migration: Add user_id to bank_log table
-- Date: 2025-11-05
-- Description: Track which user uploaded each file

BEGIN;

-- 1) Add user_id column
ALTER TABLE bank_log
ADD COLUMN IF NOT EXISTS user_id INTEGER;

-- 2) Add foreign key constraint (SET NULL on delete to keep history)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_bank_log_user'
    ) THEN
        ALTER TABLE bank_log
        ADD CONSTRAINT fk_bank_log_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE SET NULL;
    END IF;
END $$;

-- 3) Add index for faster filtering by user
CREATE INDEX IF NOT EXISTS idx_bank_log_user_id
    ON bank_log(user_id);

-- 4) Add composite index for user + company filtering
CREATE INDEX IF NOT EXISTS idx_bank_log_user_company
    ON bank_log(user_id, company_id);

COMMIT;

-- Optional: Verify the changes
-- \d bank_log
-- SELECT conname, contype FROM pg_constraint WHERE conrelid = 'bank_log'::regclass;
