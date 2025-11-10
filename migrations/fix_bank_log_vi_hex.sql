-- Normalize Vietnamese text in bank_log fields using UTF-8 hex to avoid client encoding issues
-- Fields affected: filename, original_filename, detected_keywords (text[])
-- Safe to run multiple times; uses idempotent replacements

BEGIN;

-- 1) filename/original_filename: "Mau_so_phu" -> "Mẫu_sổ_phụ"
UPDATE public.bank_log
SET original_filename = replace(
        original_filename,
        'Mau_so_phu',
        convert_from(decode('4de1baab755f73e1bb955f7068e1bba5','hex'),'UTF8')
    )
WHERE original_filename LIKE '%Mau_so_phu%';

UPDATE public.bank_log
SET filename = replace(
        filename,
        'Mau_so_phu',
        convert_from(decode('4de1baab755f73e1bb955f7068e1bba5','hex'),'UTF8')
    )
WHERE filename LIKE '%Mau_so_phu%';

-- 2) filename/original_filename: "Mau so phu" -> "Mẫu sổ phụ"
UPDATE public.bank_log
SET original_filename = replace(
        original_filename,
        'Mau so phu',
        convert_from(decode('4de1baab752073e1bb95207068e1bba5','hex'),'UTF8')
    )
WHERE original_filename LIKE '%Mau so phu%';

UPDATE public.bank_log
SET filename = replace(
        filename,
        'Mau so phu',
        convert_from(decode('4de1baab752073e1bb95207068e1bba5','hex'),'UTF8')
    )
WHERE filename LIKE '%Mau so phu%';

-- 3) filename/original_filename: fix mojibake of "Sổ phụ" folder name
-- Replace "Sß╗ò phß╗Ñ" -> "Sổ phụ"
UPDATE public.bank_log
SET original_filename = replace(
        original_filename,
        'Sß╗ò phß╗Ñ',
        convert_from(decode('53e1bb95207068e1bba5','hex'),'UTF8')
    )
WHERE original_filename LIKE '%Sß╗ò phß╗Ñ%';

UPDATE public.bank_log
SET filename = replace(
        filename,
        'Sß╗ò phß╗Ñ',
        convert_from(decode('53e1bb95207068e1bba5','hex'),'UTF8')
    )
WHERE filename LIKE '%Sß╗ò phß╗Ñ%';

-- 4) filename/original_filename: fix mojibake of combined phrase "Mẫu sổ phụ"
-- Replace "Mß║½u sß╗ò phß╗Ñ" -> "Mẫu sổ phụ"
UPDATE public.bank_log
SET original_filename = replace(
        original_filename,
        'Mß║½u sß╗ò phß╗Ñ',
        convert_from(decode('4de1baab752073e1bb95207068e1bba5','hex'),'UTF8')
    )
WHERE original_filename LIKE '%Mß║½u sß╗ò phß╗Ñ%';

UPDATE public.bank_log
SET filename = replace(
        filename,
        'Mß║½u sß╗ò phß╗Ñ',
        convert_from(decode('4de1baab752073e1bb95207068e1bba5','hex'),'UTF8')
    )
WHERE filename LIKE '%Mß║½u sß╗ò phß╗Ñ%';

-- 5) detected_keywords text[]: fix mojibake for company name
-- "C├┤ng ty TNHH c├┤ng nghß╗ç EPI Viß╗çt Nam" -> "Công ty TNHH công nghệ EPI Việt Nam"
UPDATE public.bank_log
SET detected_keywords = array_replace(
        detected_keywords,
        'C├┤ng ty TNHH c├┤ng nghß╗ç EPI Viß╗çt Nam',
        convert_from(decode('43c3b46e6720747920544e48482063c3b46e67206e6768e1bb8720455049205669e1bb8774204e616d','hex'),'UTF8')
    )
WHERE detected_keywords::text LIKE '%C├┤ng ty TNHH c├┤ng nghß╗ç EPI Viß╗çt Nam%';

-- 6) detected_keywords text[]: fix mojibake for bank name
-- "NG├éN H├ÇNG TMCP QU├éN ─Éß╗ÿI" -> "NGÂN HÀNG TMCP QUÂN ĐỘI"
UPDATE public.bank_log
SET detected_keywords = array_replace(
        detected_keywords,
        'NG├éN H├ÇNG TMCP QU├éN ─Éß╗ÿI',
        convert_from(decode('4e47c3824e2048c3804e4720544d4350205155c3824e20c490e1bb9849','hex'),'UTF8')
    )
WHERE detected_keywords::text LIKE '%NG├éN H├ÇNG TMCP QU├éN ─Éß╗ÿI%';

COMMIT;

-- Optional verification queries (uncomment to inspect results)
-- SELECT id, original_filename FROM public.bank_log WHERE original_filename ~ '(Mau|Mß║½u|Sß╗ò)';
-- SELECT id, filename FROM public.bank_log WHERE filename ~ '(Mau|Mß║½u|Sß╗ò)';
-- SELECT id, detected_keywords FROM public.bank_log WHERE detected_keywords::text ~ 'C├┤ng|NG├éN';
