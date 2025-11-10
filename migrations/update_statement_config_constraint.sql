-- Migration: Update bank_statement_config unique constraint
-- Purpose: Allow multiple configs per bank_code (differentiated by identify_info)
-- Date: 2025-11-10

-- Drop old constraint
ALTER TABLE bank_statement_config 
DROP CONSTRAINT IF EXISTS unique_company_statement_config;

-- Add new constraint with identify_info
ALTER TABLE bank_statement_config 
ADD CONSTRAINT unique_company_statement_config_field 
UNIQUE (company_id, bank_code, identify_info);

-- Verify the change
SELECT 
    conname AS constraint_name,
    contype AS constraint_type,
    pg_get_constraintdef(oid) AS constraint_definition
FROM pg_constraint
WHERE conrelid = 'bank_statement_config'::regclass
  AND conname LIKE '%unique%';
