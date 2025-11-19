import os
import re
import pandas as pd
from datetime import datetime
from flask import current_app

from models.bank_statement_config import BankStatementConfig
from models.statement_log import StatementLog
from models.bank_log import BankLog
import os


def validate_statement_data(parsed_data):
    """
    Validate parsed statement data for required fields

    Args:
        parsed_data: Dictionary containing parsed statement information

    Returns:
        tuple: (is_valid: bool, errors: list of error messages)
    """
    errors = []

    # Check required header fields
    if not parsed_data.get('opening_balance'):
        errors.append("❌ Thiếu thông tin Số dư đầu kỳ (Opening Balance)")

    if not parsed_data.get('closing_balance'):
        errors.append("❌ Thiếu thông tin Số dư cuối kỳ (Closing Balance)")

    if not parsed_data.get('currency'):
        errors.append("❌ Thiếu thông tin Loại tiền (Currency)")

    if not parsed_data.get('bank_code'):
        errors.append("❌ Thiếu thông tin Tên ngân hàng (Bank Code)")

    # Note: Account number is now optional - if missing, user will be prompted to enter it
    # This is intentional to allow manual entry

    # Check transaction data
    transactions = parsed_data.get('transactions', [])

    if not transactions or len(transactions) == 0:
        errors.append("❌ Không tìm thấy giao dịch nào trong file. Phải có tối thiểu 1 giao dịch hợp lệ.")
    else:
        # Check each transaction for required fields
        missing_fields_summary = {
            'credit_debit_fee_vat': 0,
            'narrative': 0,
            'transaction_date': 0
        }

        valid_transactions = 0

        for idx, txn in enumerate(transactions, 1):
            # At least one of credit or debit must have value
            credit = txn.get('credit') or txn.get('creditmoney')
            debit = txn.get('debit') or txn.get('debitmoney')
            transactionfee = txn.get('transactionfee')
            transactionvat= txn.get('transactionvat')
            has_credit_debit_fee_vat = False
            if credit or debit or transactionfee or transactionvat:
                try:
                    # Check if it's a valid number (not empty string)
                    if credit and str(credit).strip():
                        float(str(credit).replace(',', ''))
                        has_credit_debit_fee_vat = True
                    if debit and str(debit).strip():
                        float(str(debit).replace(',', ''))
                        has_credit_debit_fee_vat = True
                    if transactionfee and str(transactionfee).strip():
                        float(str(transactionfee).replace(',', ''))
                        has_credit_debit_fee_vat = True
                    if transactionvat and str(transactionvat).strip():
                        float(str(transactionvat).replace(',', ''))
                        has_credit_debit_fee_vat = True
                except (ValueError, TypeError):
                    pass

            if not has_credit_debit_fee_vat:
                missing_fields_summary['credit_debit_fee_vat'] += 1

            # Check narrative
            narrative = txn.get('narrative') or txn.get('detail') or txn.get('description')
            if not narrative or not str(narrative).strip():
                missing_fields_summary['narrative'] += 1

            # Check transaction date
            txn_date = txn.get('transactiondate') #or txn.get('valuedate') or txn.get('date')
            if not txn_date or not str(txn_date).strip():
                missing_fields_summary['transaction_date'] += 1

            # Count as valid if it has all 4 required fields
            if has_credit_debit_fee_vat and narrative and str(narrative).strip() and txn_date and str(txn_date).strip():
                valid_transactions += 1

        # Report summary of missing fields
        if valid_transactions == 0:
            errors.append(f"❌ Không có giao dịch hợp lệ nào. Mỗi giao dịch phải có: Transaction Date, Narrative, và Credit/Debit/Fee/VAT")

        if missing_fields_summary['credit_debit_fee_vat'] > 0:
            errors.append(f"⚠️ Thiếu thông tin Credit/Debit/Fee/VAT cho {missing_fields_summary['credit_debit_fee_vat']}/{len(transactions)} giao dịch")

        if missing_fields_summary['narrative'] > 0:
            errors.append(f"⚠️ Thiếu thông tin Narrative (Diễn giải) cho {missing_fields_summary['narrative']}/{len(transactions)} giao dịch")

        if missing_fields_summary['transaction_date'] > 0:
            errors.append(f"⚠️ Thiếu thông tin Transaction Date (Ngày giao dịch) cho {missing_fields_summary['transaction_date']}/{len(transactions)} giao dịch")

    is_valid = len(errors) == 0

    return is_valid, errors


def _col_to_index(col_str):
    """Convert Excel-style column (A, B, AA) to 0-based index. If numeric string, return int-1."""
    if not col_str:
        return None
    s = str(col_str).strip()
    if s.isdigit():
        return max(0, int(s) - 1)
    s = s.upper()
    idx = 0
    for ch in s:
        if 'A' <= ch <= 'Z':
            idx = idx * 26 + (ord(ch) - ord('A') + 1)
        else:
            return None
    return idx - 1


def _get_dataframe_sheets(path, ext):
    ext = ext.lower()
    if ext in ("xls", "xlsx"):
        xls = pd.read_excel(path, sheet_name=None, dtype=str)
        # normalize to dict of sheetname -> df
        return xls
    elif ext == 'csv':
        df = pd.read_csv(path, dtype=str)
        return {'sheet1': df}
    else:
        # Not a tabular file
        return {}


def _find_value_in_df(df, keywords, col_keyword, col_value, row_start, row_end, identify_info):
    # df: pandas DataFrame
    # keywords: list
    # column selectors may be header names or column letters
    # identif
    if df is None or df.shape[0] == 0:
        return None

    # determine start/end indices (0-based)
    nrows = df.shape[0]
    if row_start and row_start > 0:
        start = max(0, row_start - 1)
    else:
        start = 0
    if row_end and row_end > 0:
        end = min(nrows - 1, row_end - 1)
    else:
        end = nrows - 1

    # resolve column for keyword and value
    kw_col = None
    val_col = None

    if col_keyword:
        if col_keyword in df.columns:
            kw_col = col_keyword
        else:
            idx = _col_to_index(col_keyword)
            if idx is not None and idx < len(df.columns):
                kw_col = df.columns[idx]

    if col_value:
        if col_value in df.columns:
            val_col = col_value
        else:
            idx = _col_to_index(col_value)
            if idx is not None and idx < len(df.columns):
                val_col = df.columns[idx]

    # Check if col_keyword == col_value (same column for both keyword and value)
    same_column = (col_keyword == col_value) and col_keyword is not None

    # If no kw_col but val_col provided, we try to read first matching row by keywords anywhere
    for r in range(start, end + 1):
        row = df.iloc[r]
        row_text = ' '.join([str(x) for x in row.tolist() if x is not None])
        found = False
        matched_keyword = None

        for kw in (keywords or []):
            if kw and kw.lower() in str(row_text).lower():
                found = True
                matched_keyword = kw
                break

        if found:
            # pick value
            raw_value = None
            if val_col:
                raw_value = str(row.get(val_col, '')).strip()
            elif kw_col:
                raw_value = str(row.get(kw_col, '')).strip()
            else:
                # return whole row as string
                raw_value = row_text

            # SMART EXTRACTION when col_keyword == col_value (same column)
            if same_column and identify_info and raw_value:
                ident_lower = str(identify_info).lower().strip()

                # Account Number: search for keywords then extract 4-20 digit pattern
                if ident_lower == 'accountno':
                    # If a keyword was matched, search near the keyword
                    if matched_keyword:
                        kw_lower = matched_keyword.lower()
                        text_lower = raw_value.lower()
                        kw_idx = text_lower.find(kw_lower)

                        if kw_idx != -1:
                            # Extract text after keyword
                            after_keyword = raw_value[kw_idx + len(matched_keyword):]
                            # Find first 4-20 consecutive digits after keyword
                            match = re.search(r'\b(\d{4,20})\b', after_keyword)
                            if match:
                                return match.group(1)

                    # Fallback: search entire raw_value for 4-20 digit pattern
                    match = re.search(r'\b(\d{4,20})\b', raw_value)
                    if match:
                        return match.group(1)

                    # Last resort: extract all digits and check length
                    digits = re.sub(r'\D', '', raw_value)
                    if 4 <= len(digits) <= 20:
                        return digits

                # Currency: extract 3 alphabetic characters (like VND, USD, EUR)
                elif ident_lower == 'currency':
                    # List of valid ISO 4217 currency codes (most common ones)
                    valid_currencies = {
                        'VND', 'USD', 'EUR', 'GBP', 'CAD', 'CNY', 'AUD', 'MYR',
                        'IDR', 'THB', 'JPY', 'KRW', 'SGD', 'HKD', 'TWD', 'PHP',
                        'INR', 'CHF', 'NZD', 'SEK', 'NOK', 'DKK', 'PLN', 'RUB',
                        'BRL', 'MXN', 'ZAR', 'TRY', 'AED', 'SAR', 'QAR', 'KWD'
                    }

                    # Find 3 consecutive letters
                    matches = re.findall(r'\b([A-Za-z]{3})\b', raw_value)
                    for match in matches:
                        currency_code = match.upper()
                        if currency_code in valid_currencies:
                            return currency_code

                    # If no valid currency found in list, return None
                    return None

                # Opening/Closing Balance: extract number after keyword (exclude currency unit)
                elif ident_lower in ('openingbalance', 'closingbalance'):
                    if matched_keyword:
                        # Find keyword position in text
                        text_lower = raw_value.lower()
                        kw_idx = text_lower.find(matched_keyword.lower())
                        if kw_idx != -1:
                            # Text after keyword
                            after_keyword = raw_value[kw_idx + len(matched_keyword):]
                            # Patterns to find numeric token (thousand separators allowed), avoid trailing currency code
                            patterns = [
                                r'[:\s]*([0-9][0-9,\.]*)'  # fallback
                            ]
                            for pat in patterns:
                                match = re.search(pat, after_keyword)
                                if match:
                                    raw_num = match.group(1).strip()
                                    # Remove thousand separators
                                    cleaned = re.sub(r'[,.]', '', raw_num)
                                    # Strip any trailing currency code remnants just in case
                                    cleaned = re.sub(r'(VND|USD|EUR|GBP|CAD|CNY|AUD|MYR|IDR|THB|JPY|KRW|SGD|HKD|TWD|PHP|INR|CHF|NZD|SEK|NOK|DKK|PLN|RUB|BRL|MXN|ZAR|TRY|AED|SAR|QAR|KWD)$', '', cleaned, flags=re.I).strip()
                                    if cleaned:
                                        return cleaned

            # Return raw value if no smart extraction applied or no match found
            return raw_value

    return None


def parse_and_store_statement(session, file_path, original_filename, ext, company_id, bank_code, user_id):
    """Parse statement according to BankStatementConfig rules and store StatementLog + MT940 file.

    Assumptions (based on repository config fields):
    - Each BankStatementConfig.identify_info is the target field name (e.g. accountno, currency, openingbalance,
      closingbalance, transactiondate, narrative, debit, credit, flowcode, transactionfee, transactionvat)
    - For header fields we expect a single value extracted via col_keyword/col_value and keywords.
    - For detail fields we read vertically across a row range and assemble rows.
    """
    try:
        configs = session.query(BankStatementConfig).filter_by(company_id=company_id, bank_code=bank_code).all()

        sheets = _get_dataframe_sheets(file_path, ext)

        header_fields = ['accountno', 'currency', 'openingbalance', 'closingbalance']
        detail_fields = ['transactiondate', 'narrative', 'debit', 'credit', 'flowcode', 'transactionfee', 'transactionvat', 'reference_number']

        header: dict[str, str | None] = {k: None for k in header_fields}
        # mapping identify_info -> list of configs (usually one)
        detail_mappings = {}

        for cfg in configs:
            ident = (cfg.identify_info or '').strip().lower()
            if ident in header_fields:
                # try find value across sheets
                val = None
                for name, df in sheets.items():
                    val = _find_value_in_df(df, cfg.keywords or [], cfg.col_keyword, cfg.col_value, cfg.row_start, cfg.row_end, ident)
                    if val:
                        break
                header[ident] = val
            elif ident in detail_fields:
                detail_mappings[ident] = cfg

        # Build detail rows by scanning sheets and using the row range from first mapping found
        details = []
        # If any detail mapping exists, take its row range (fallback to None)
        any_cfg = next(iter(detail_mappings.values()), None)
        if any_cfg:
            # use the first sheet that yields rows
            for name, df in sheets.items():
                if df is None or df.shape[0] == 0:
                    continue
                nrows = df.shape[0]
                start = (any_cfg.row_start - 1) if any_cfg.row_start else 0
                end = (any_cfg.row_end - 1) if any_cfg.row_end else (nrows - 1)
                start = max(0, start)
                end = min(nrows - 1, end)

                for r in range(start, end + 1):
                    row = df.iloc[r]
                    # decide if row looks like a transaction row by checking transactiondate or keywords
                    row_text = ' '.join([str(x) for x in row.tolist() if x is not None])
                    is_empty = not row_text.strip()
                    if is_empty:
                        continue
                    trx = {}
                    any_value = False
                    for field, cfg in detail_mappings.items():
                        # if col_value present, use it; if not and col_keyword present, use that column vertically
                        val = None
                        # prefer value column first
                        if cfg.col_value:
                            # resolve actual col
                            if cfg.col_value in df.columns:
                                val = row.get(cfg.col_value)
                            else:
                                idx = _col_to_index(cfg.col_value)
                                if idx is not None and idx < len(df.columns):
                                    val = row.iloc[idx]
                        elif cfg.col_keyword:
                            # if col_keyword present and col_value empty -> treat col_keyword as the data column
                            if cfg.col_keyword in df.columns:
                                val = row.get(cfg.col_keyword)
                            else:
                                idx = _col_to_index(cfg.col_keyword)
                                if idx is not None and idx < len(df.columns):
                                    val = row.iloc[idx]
                        if val is not None and (str(val).strip() != ''):
                            any_value = True
                        trx[field] = None if pd.isna(val) else (str(val).strip() if val is not None else None)

                    if any_value:
                        # Normalize/validate transaction date: parse and format to ddmmyyyy (day-first)
                        raw_td = trx.get('transactiondate')
                        raw_narrative = trx.get('narrative')

                        # STRICT FILTER: Only include rows where:
                        # 1. transactiondate is a valid date/datetime format
                        # 2. narrative is not empty
                        parsed_td = None
                        if raw_td and str(raw_td).strip():
                            try:
                                # parse with dayfirst=True to prefer dd/mm/YYYY style
                                dt = pd.to_datetime(str(raw_td).strip(), dayfirst=True, errors='coerce')
                                if not pd.isna(dt):
                                    parsed_td = dt.strftime('%d%m%Y')
                            except Exception:
                                parsed_td = None

                        # Check narrative is not empty
                        has_valid_narrative = raw_narrative and str(raw_narrative).strip() != ''

                        # Only append rows where BOTH conditions are met:
                        # - parsed transaction date is valid (non-null)
                        # - narrative is not empty
                        if parsed_td and has_valid_narrative:
                            trx['transactiondate'] = parsed_td
                            details.append(trx)

                # stop after first sheet with data
                if details:
                    break

        # Before creating StatementLog, sort details by transactiondate ascending (earliest first)
        def _parse_date_for_sort(dct):
            td = dct.get('transactiondate')
            if not td:
                return pd.Timestamp.max
            try:
                dt = pd.to_datetime(td, errors='coerce')
                if pd.isna(dt):
                    return pd.Timestamp.max
                return dt
            except Exception:
                return pd.Timestamp.max

        if details:
            try:
                details = sorted(details, key=_parse_date_for_sort)
            except Exception:
                # fallback: keep original order on any failure
                pass

        # ===== VALIDATION: Check required fields =====
        validation_data = {
            'opening_balance': header.get('openingbalance'),
            'closing_balance': header.get('closingbalance'),
            'currency': header.get('currency'),
            'bank_code': bank_code,
            'account_number': header.get('accountno'),
            'transactions': details
        }

        is_valid, validation_errors = validate_statement_data(validation_data)

        if not is_valid:
            # Check if error is ONLY missing account number
            # If so, we'll create the StatementLog and let user edit it later
            account_only_error = (
                len(validation_errors) == 0 or
                all('account' in err.lower() or 'tài khoản' in err.lower() for err in validation_errors)
            )

            if not account_only_error:
                # Critical validation errors (not just missing account) - delete file and return error
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception:
                    pass

                # Delete associated BankLog if exists
                try:
                    bl = session.query(BankLog).filter_by(filename=file_path).first()
                    if bl:
                        session.delete(bl)
                        session.commit()
                except Exception:
                    pass

                error_message = "Mẫu sổ phụ không hợp lệ"
                current_app.logger.warning(f"Statement validation failed: {validation_errors}")

                return {
                    "status": "INVALID",
                    "message": error_message,
                    "errors": validation_errors
                }
            # If only account is missing, continue to create StatementLog below
        # ===== END VALIDATION =====

        # Validate balances: compute totals and ensure closing balance matches expected.
        # Totals: sum credits, sum debits, sum fees, sum vat (all numeric via float_safe)
        try:
            # Select eligible rows: must have transactiondate AND non-empty narrative
            # and at least one of credit/debit/transactionfee/transactionvat present (non-zero after float_safe)
            eligible = []
            for d in details:
                if not d:
                    continue
                tdate = d.get('transactiondate')
                narrative_val = d.get('narrative')
                if not tdate or not (narrative_val and str(narrative_val).strip()):
                    continue
                # check numeric fields
                c = float_safe(d.get('credit') or 0)
                rr = float_safe(d.get('debit') or 0)
                f = float_safe(d.get('transactionfee') or 0)
                v = float_safe(d.get('transactionvat') or 0)
                if any(abs(x) > 0.0 for x in (c, rr, f, v)):
                    eligible.append(d)

            if eligible:
                total_credit = sum(abs(float_safe(d.get('credit') or 0)) for d in eligible)
                total_debit = sum(abs(float_safe(d.get('debit') or 0)) for d in eligible)
                total_fee = sum(abs(float_safe(d.get('transactionfee') or 0)) for d in eligible)
                total_vat = sum(abs(float_safe(d.get('transactionvat') or 0)) for d in eligible)
            else:
                # no eligible rows -> skip balance validation
                total_credit = total_debit = total_fee = total_vat = None
        except Exception:
            total_credit = total_debit = total_fee = total_vat = None

        opening_val = float_safe(header.get('openingbalance') or 0)
        closing_val = float_safe(header.get('closingbalance') or 0)

        # If totals are None, we skip validation
        if total_credit is not None and total_debit is not None and total_fee is not None and total_vat is not None:
            # Số dư phát sinh = Credit - Debit - Fee - VAT
            so_du_phat_sinh = total_credit - total_debit - total_fee - total_vat
            expected_closing = opening_val + so_du_phat_sinh

            # allow small epsilon for floating point rounding (1e-2 => cents)
            if abs(expected_closing - closing_val) > 0.01:
                # On mismatch: remove the uploaded file and any BankLog referencing it, then return INVALID
                try:
                    # delete file from filesystem if exists
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception:
                    pass
                try:
                    # remove BankLog entries that reference this filename to avoid stale logs
                    session.query(BankLog).filter(BankLog.filename == file_path).delete(synchronize_session=False)
                    session.commit()
                except Exception:
                    session.rollback()

                # Build detailed error message
                error_details = [
                    "❌ Số dư cuối kỳ <> Số dư phát sinh + Số dư đầu kỳ",
                    "",
                    "📊 Chi tiết:",
                    f"   • Số dư đầu kỳ (Opening Balance): {opening_val:,.2f}",
                    f"   • Tổng Credit: {total_credit:,.2f}",
                    f"   • Tổng Debit: {total_debit:,.2f}",
                    f"   • Tổng Fee: {total_fee:,.2f}",
                    f"   • Tổng VAT: {total_vat:,.2f}",
                    f"   • Số dư phát sinh = Credit - Debit - Fee - VAT = {so_du_phat_sinh:,.2f}",
                    "",
                    f"🔢 Kết quả:",
                    f"   • Số dư cuối kỳ TÍNH ĐƯỢC = Số dư đầu kỳ + Số dư phát sinh = {opening_val:,.2f} + {so_du_phat_sinh:,.2f} = {expected_closing:,.2f}",
                    f"   • Số dư cuối kỳ TRONG FILE (Closing Balance) = {closing_val:,.2f}",
                    f"   • Chênh lệch = {abs(expected_closing - closing_val):,.2f}",
                ]

                msg = "\n".join(error_details)

                return {
                    "status": "INVALID",
                    "message": "Số dư cuối kỳ khác Số dư phát sinh + Số dư đầu kỳ",
                    "errors": error_details
                }

        # Normalize account number and other header fields: treat pandas NaN, empty strings,
        # and common null tokens as missing (store as None) so downstream logic can detect missing accounts.
        def _normalize_field(v):
            try:
                # pandas NA/NaN
                if pd.isna(v):
                    return None
            except Exception:
                pass
            if v is None:
                return None
            s = str(v).strip()
            if s == '':
                return None
            if s.lower() in ('nan', 'nat', 'none', 'null'):
                return None
            return s

        account_norm = _normalize_field(header.get('accountno'))
        currency_norm = _normalize_field(header.get('currency'))
        opening_norm = _normalize_field(header.get('openingbalance'))
        closing_norm = _normalize_field(header.get('closingbalance'))

        # create StatementLog
        stmt_log = StatementLog(
            user_id=user_id, # type: ignore
            company_id=company_id, # type: ignore
            bank_code=bank_code, # type: ignore
            filename=file_path, # type: ignore
            original_filename=original_filename, # type: ignore
            status='SUCCESS', # type: ignore
            message='Parsed statement', # type: ignore
            accountno=account_norm, # type: ignore
            currency=currency_norm, # type: ignore
            opening_balance=opening_norm, # type: ignore
            closing_balance=closing_norm, # type: ignore
            details=details if details else None, # type: ignore
        )
        session.add(stmt_log)
        session.commit()

        # Generate MT940 text and save
        mt_text = build_mt940_strict(stmt_log)
        mt_dir = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), 'mt940')
        os.makedirs(mt_dir, exist_ok=True)
        ts = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        safe_name = (original_filename or 'statement').rsplit('.', 1)[0]
        mt_filename = f"{safe_name}_{bank_code}_{ts}.mt940.txt"
        mt_path = os.path.join(mt_dir, mt_filename)
        with open(mt_path, 'w', encoding='utf-8') as f:
            f.write(mt_text)

        # store relative path
        rel_path = os.path.relpath(mt_path, current_app.config.get('UPLOAD_FOLDER', 'uploads'))
        stmt_log.mt940_filename = rel_path.replace('\\', '/')
        session.commit()

        return {"status": "SUCCESS", "statement_log_id": stmt_log.id, "mt940": stmt_log.mt940_filename}

    except Exception as e:
        # create failed statement log
        session.rollback()
        try:
            log = StatementLog(
                user_id=user_id, # type: ignore
                company_id=company_id, # type: ignore
                bank_code=bank_code, # type: ignore
                original_filename=original_filename, # type: ignore
                status='FAILED', # type: ignore
                message=str(e) # type: ignore
            )
            session.add(log)
            session.commit()
        except Exception:
            session.rollback()
        return {"status": "FAILED", "message": str(e)}


def _format_amount_mt940(value):
    """Format a numeric amount for MT940: no thousands separator, decimal comma, 2 decimals.

    Example: 1234.5 -> '1234,50'
    """
    try:
        v = float(str(value).replace(',', '').strip())
    except Exception:
        return '0'
    # If the amount is a whole number, return integer string (no decimal separator) like sample
    if abs(v - int(v)) < 0.000001:
        return str(int(v))
    # otherwise format with 2 decimals and comma as decimal separator
    formatted = f"{v:0.2f}".replace('.', ',')
    return formatted


def build_mt940_strict(stmt_log):
    """Build an MT940-ish text following common field patterns.

    This produces fields: :20:, :25:, :28C:, :60F:, multiple :61:/:86:, :62F:
    It's pragmatic but tries to follow MT940 structure and date/amount formats.
    """
    lines = []
    # :20: – transaction reference. Use bank_code + 'XXX' as requested.
    bank_code = (stmt_log.bank_code or 'UNK').upper()
    ref = f"{bank_code}VNXXX"
    lines.append(f":20:{ref}")
    if stmt_log.accountno:
        lines.append(f":25:{stmt_log.accountno}")
    # Statement number (use zero-padded sample style)
    lines.append(f":28C:00000/001")

    # determine statement date range — prefer earliest (min) and latest (max) transaction dates if available
    currency = (stmt_log.currency or '').upper()
    filtered_details = [d for d in (stmt_log.details or []) if d.get('transactiondate') and (d.get('narrative') and str(d.get('narrative')).strip())]
    min_dt = None
    max_dt = None
    for d in filtered_details:
        td = d.get('transactiondate')
        if td:
            try:
                dt = pd.to_datetime(td, errors='coerce')
                if not pd.isna(dt):
                    if min_dt is None or dt < min_dt:
                        min_dt = dt
                    if max_dt is None or dt > max_dt:
                        max_dt = dt
            except Exception:
                pass

    min_date_str = min_dt.strftime('%y%m%d') if min_dt is not None else datetime.utcnow().strftime('%y%m%d')
    max_date_str = max_dt.strftime('%y%m%d') if max_dt is not None else datetime.utcnow().strftime('%y%m%d')
    ob = stmt_log.opening_balance or '0'
    cb = stmt_log.closing_balance or '0'
    # assume positive closing/opening are credits (C)
    lines.append(f":60F:C{min_date_str}{currency}{_format_amount_mt940(ob)}")

    # transactions - build stricter :61: and :86: lines
    seq = 1
    # Only include transactions that have a transactiondate and a non-empty narrative
    # filtered_details already computed above; reuse if available
    try:
        filtered_details # type: ignore
    except NameError:
        filtered_details = [d for d in (stmt_log.details or []) if d.get('transactiondate') and (d.get('narrative') and str(d.get('narrative')).strip())]
    for d in filtered_details:
        tdate = d.get('transactiondate') or ''
        narrative = (d.get('narrative') or '').strip()
        # If flowcode exists, prepend it to narrative as "flowcode_narrative"
        flowcode_val = (d.get('flowcode') or '').strip()
        if flowcode_val:
            if narrative:
                narrative = f"{flowcode_val}_{narrative}"
            else:
                narrative = f"{flowcode_val}"
        debit = d.get('debit') or ''
        credit = d.get('credit') or ''

        # determine amount and D/C flag
        # D = Debit (money out), C = Credit (money in)
        amt = 0.0
        dc_flag = 'C'
        # parse fee/vat if present
        fee = float_safe(d.get('transactionfee') or 0)
        vat = float_safe(d.get('transactionvat') or 0)

        # Robust numeric parsing: prefer credit when credit value is present and non-zero.
        v_credit = float_safe(credit)
        v_debit = float_safe(debit)

        # If credit is present and non-zero -> credit
        if v_credit != 0:
            if v_credit < 0:
                dc_flag = 'D'
                amt = abs(v_credit)
            else:
                dc_flag = 'C'
                amt = v_credit
        else:
            # else consider debit (including fees/vat)
            total_debit = v_debit + fee + vat
            if total_debit != 0:
                dc_flag = 'D'
                amt = abs(total_debit)

        # format amount for MT940 (no thousand sep, comma decimal)
        amt_str = _format_amount_mt940(amt)

        # parse transaction date to YYMMDD format (MT940 standard)
        date_str = ''
        if tdate:
            try:
                # First try exact format produced during ingestion: 'ddmmyyyy'
                dt = pd.to_datetime(tdate, format='%d%m%Y', errors='coerce')
                if pd.isna(dt):
                    # fallback to flexible parse with dayfirst
                    dt = pd.to_datetime(tdate, dayfirst=True, errors='coerce')
                if not pd.isna(dt):
                    date_str = dt.strftime('%y%m%d')  # YYMMDD format
            except Exception:
                date_str = ''
        # If date_str still empty, fall back to statement-level min date so :61 always includes a date
        if not date_str:
            try:
                # min_date_str already in YYMMDD format
                md = pd.to_datetime(min_date_str, format='%y%m%d', errors='coerce')
                date_str = md.strftime('%y%m%d') if not pd.isna(md) else datetime.utcnow().strftime('%y%m%d')
            except Exception:
                date_str = datetime.utcnow().strftime('%y%m%d')
        # transaction type: prefer an explicit transaction type from data, else default to 'NTRF'
        trx_type = (d.get('transactiontype') or d.get('trx_type') or 'NTRF')
        trx_type = str(trx_type).strip().upper()
        # bank reference from parsed details (support common alternative keys)
        bank_ref = d.get('reference_number') or d.get('bank_reference') or d.get('reference') or d.get('ref') or d.get('bankref')
        bank_ref = str(bank_ref).strip() if bank_ref is not None else ''
        # If bank_ref exists, include REF token + //bank_ref; otherwise omit REF and suffix entirely
        if bank_ref:
            ref_part = 'NONREF'
            ref_suffix = f"//{bank_ref}"
            trailing = f"{ref_part}{ref_suffix}"
        else:
            trailing = ''
        # Build :61 in requested style WITHOUT spaces: DDMMYYYY + D/C + amount + TRX_TYPE + [REF//bankref]
        line61 = f":61:{date_str}{dc_flag}{amt_str}{trailing}"
        lines.append(line61)

        # :86: - narrative free text. Emit exactly one :86: line per transaction.
        if narrative:
            clean = ' '.join(narrative.split())
            # limit to a reasonable length (200 chars) to avoid oversized tag
            clean = clean[:200]
            lines.append(f":86:{clean}")

        seq += 1

    # closing balance uses latest transaction date
    lines.append(f":62F:C{max_date_str}{currency}{_format_amount_mt940(cb)}")
    return '\n'.join(lines)


def float_safe(s):
    """Safely convert string to float, handling various formats.

    Supports:
    - Plain numbers: "1234.56"
    - Thousand separators: "7,529,778,893" or "7.529.778.893"
    - Currency symbols: "7,529,778,893 VND"
    - Descriptive text: "Opening Balance: 7,529,778,893 VND"
    - Accounting negatives: "(1234.56)"
    """
    import re

    try:
        s = str(s)
        if not s:
            return 0.0
        s = s.strip()
        if s == '':
            return 0.0

        # Try to extract amount from descriptive text first
        # Pattern to find numbers with optional commas/dots as thousands separators
        patterns = [
            r':\s*([\d,\.]+)\s*VND',  # After colon, before VND
            r':\s*([\d,\.]+)',         # After colon
            r'([\d,\.]+)\s*VND',       # Before VND
            r'\b(\d{1,3}(?:[,\.]\d{3})+)\b',  # Numbers with thousand separators
            r'\b(\d+)\b',              # Plain numbers
        ]

        for pattern in patterns:
            match = re.search(pattern, s)
            if match:
                num_str = match.group(1)
                # Remove all commas and dots that are thousand separators
                cleaned = re.sub(r'[,\.]', '', num_str)
                try:
                    return float(cleaned)
                except ValueError:
                    continue

        # Fallback to simple parsing
        # handle parentheses (accounting negative format)
        negative = False
        if s.startswith('(') and s.endswith(')'):
            negative = True
            s = s[1:-1]

        # remove common currency symbols, non-breaking space and normal spaces
        for ch in ['$', '€', '£', '\xa0', ' ', 'VND', 'USD', 'EUR','GBP', 'CAD', 'CNY', 'AUD', 'MYR',
                        'IDR', 'THB', 'JPY', 'KRW', 'SGD', 'HKD', 'TWD', 'PHP',
                        'INR', 'CHF', 'NZD', 'SEK', 'NOK', 'DKK', 'PLN', 'RUB',
                        'BRL', 'MXN', 'ZAR', 'TRY', 'AED', 'SAR', 'QAR', 'KWD']:
            s = s.replace(ch, '')

        # remove thousands separators commonly using comma
        s = s.replace(',', '')
        v = float(s)
        return -v if negative else v
    except Exception:
        return 0.0
