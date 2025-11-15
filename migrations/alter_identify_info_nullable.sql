-- Migration: Cho phép identify_info nullable trong bank_statement_config
-- Ngày: 2025-11-10

-- Bước 1: Bỏ constraint unique cũ (nếu có)
ALTER TABLE bank_statement_config DROP CONSTRAINT IF EXISTS unique_company_statement_config_field;

-- Bước 2: Cho phép identify_info NULL
ALTER TABLE bank_statement_config ALTER COLUMN identify_info DROP NOT NULL;

-- Bước 3: Tạo lại constraint unique mới (có thể NULL)
-- Lưu ý: Trong PostgreSQL, NULL không bị coi là duplicate trong unique constraint
-- Nếu cần logic phức tạp hơn, có thể tạo unique index với WHERE clause
-- Ví dụ: CREATE UNIQUE INDEX idx_company_bank_identify ON bank_statement_config(company_id, bank_code, identify_info) WHERE identify_info IS NOT NULL;

-- Hoặc giữ constraint đơn giản (cho phép nhiều NULL)
ALTER TABLE bank_statement_config ADD CONSTRAINT unique_company_statement_config_field
    UNIQUE (company_id, bank_code, identify_info);

-- Bước 4: Kiểm tra constraint cell_format (nếu có lỗi với giá trị 'text', 'number', 'date')
-- Có thể cần sửa constraint này nếu nó chỉ chấp nhận chữ thường
-- Kiểm tra constraint hiện tại:
-- SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid = 'bank_statement_config'::regclass;
