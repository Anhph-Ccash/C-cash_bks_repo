-- Additional Vietnamese text fixes for bank_log
-- Handles multiple mojibake patterns from different encoding mismatches

BEGIN;

-- Fix detected_keywords array corruption patterns
-- Pattern 1: Fix the multi-byte corruption in detected_keywords
UPDATE public.bank_log
SET detected_keywords = ARRAY[convert_from(decode('4e47c3824e2048c3804e4720544d4350205155c3824e20c490e1bb9849','hex'),'UTF8')]
WHERE id = 56;

UPDATE public.bank_log
SET detected_keywords = ARRAY[convert_from(decode('43c3b46e6720747920544e48482063c3b46e67206e6768e1bb8720455049205669e1bb8774204e616d','hex'),'UTF8')]
WHERE id = 57;

-- Fix original_filename for rows with complex corruption (ids 61-114)
-- These have a different encoding corruption pattern
UPDATE public.bank_log
SET original_filename = replace(
        original_filename,
        substring(original_filename from '^[^_]+'),
        convert_from(decode('4de1baab752073e1bb95207068e1bba5','hex'),'UTF8')
    )
WHERE id BETWEEN 61 AND 114
  AND original_filename ~ '^M[^a-zA-Z]';

-- Simpler approach: directly set known patterns
UPDATE public.bank_log
SET original_filename = convert_from(decode('4de1baab752073e1bb95207068e1bba5','hex'),'UTF8') || ' _TPB.xlsx'
WHERE original_filename LIKE '%_TPB.xlsx'
  AND original_filename !~ '^Mau'
  AND encode(convert_to(original_filename,'UTF8'),'hex') LIKE '4dc383%';

UPDATE public.bank_log
SET original_filename = convert_from(decode('4de1baab752073e1bb95207068e1bba5','hex'),'UTF8') || ' _EXB.xlsx'
WHERE original_filename LIKE '%_EXB.xlsx'
  AND original_filename !~ '^Mau'
  AND encode(convert_to(original_filename,'UTF8'),'hex') LIKE '4dc383%';

UPDATE public.bank_log
SET original_filename = convert_from(decode('4de1baab752073e1bb95207068e1bba5','hex'),'UTF8') || ' _TCB.xlsx'
WHERE original_filename LIKE '%_TCB.xlsx'
  AND original_filename !~ '^Mau'
  AND encode(convert_to(original_filename,'UTF8'),'hex') LIKE '4dc383%';

-- Fix filename paths containing corrupted folder names
UPDATE public.bank_log
SET filename = regexp_replace(
        filename,
        'Sß╗ò phß╗Ñ',
        convert_from(decode('53e1bb95207068e1bba5','hex'),'UTF8'),
        'g'
    )
WHERE filename LIKE '%Sß╗ò phß╗Ñ%';

COMMIT;

-- Verify
SELECT id, original_filename,
       encode(convert_to(original_filename,'UTF8'),'hex') AS hex
FROM bank_log
WHERE id IN (56, 57, 60, 61, 62)
ORDER BY id;
