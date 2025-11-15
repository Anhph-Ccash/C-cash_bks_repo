-- Migration: Make company_id nullable in bank_log table
-- Date: 2025-11-10
-- Description: Allow bank_log entries without company_id for backward compatibility

BEGIN;

-- Remove NOT NULL constraint from company_id if it exists
ALTER TABLE bank_log
ALTER COLUMN company_id DROP NOT NULL;

COMMIT;

-- Verify
-- \d bank_log
