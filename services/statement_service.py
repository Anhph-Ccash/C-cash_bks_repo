import os
import pandas as pd
from datetime import datetime
from flask import current_app

from models.bank_statement_config import BankStatementConfig
from models.statement_log import StatementLog
from models.bank_log import BankLog
import os


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


def _find_value_in_df(df, keywords, col_keyword, col_value, row_start, row_end):
    # df: pandas DataFrame
    # keywords: list
    # column selectors may be header names or column letters
    # return first matched value or None
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

    # If no kw_col but val_col provided, we try to read first matching row by keywords anywhere
    for r in range(start, end + 1):
        row = df.iloc[r]
        row_text = ' '.join([str(x) for x in row.tolist() if x is not None])
        found = False
        for kw in (keywords or []):
            if kw and kw.lower() in str(row_text).lower():
                found = True
                break
        if found:
            # pick value
            if val_col:
                return str(row.get(val_col, '')).strip()
            elif kw_col:
                return str(row.get(kw_col, '')).strip()
            else:
                # return whole row as string
                return row_text

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

        header = {k: None for k in header_fields}
        # mapping identify_info -> list of configs (usually one)
        detail_mappings = {}

        for cfg in configs:
            ident = (cfg.identify_info or '').strip().lower()
            if ident in header_fields:
                # try find value across sheets
                val = None
                for name, df in sheets.items():
                    val = _find_value_in_df(df, cfg.keywords or [], cfg.col_keyword, cfg.col_value, cfg.row_start, cfg.row_end)
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
                        parsed_td = None
                        if raw_td and str(raw_td).strip():
                            try:
                                # parse with dayfirst=True to prefer dd/mm/YYYY style
                                dt = pd.to_datetime(str(raw_td).strip(), dayfirst=True, errors='coerce')
                                if not pd.isna(dt):
                                    parsed_td = dt.strftime('%d%m%Y')
                            except Exception:
                                parsed_td = None

                        # Only append rows where parsed transaction date is valid (non-null)
                        if parsed_td:
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
        if total_credit is not None:
            expected_closing = opening_val + total_credit - total_debit - total_fee - total_vat
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

                # Build detailed message including the computed formula and values
                msg = (
                    "Số dư cuối kỳ không khớp với số dư đầu kỳ cộng số dư phát sinh. Vui lòng kiểm tra lại! "
                    f"(Công thức: expected = opening + totalCredit - totalDebit - totalFee - totalVat)\n"
                    f"opening={opening_val:.2f}, totalCredit={total_credit:.2f}, totalDebit={total_debit:.2f}, totalFee={total_fee:.2f}, totalVat={total_vat:.2f} -> expected_closing={expected_closing:.2f}, closing={closing_val:.2f}"
                )

                return {"status": "INVALID", "message": msg}

        # create StatementLog
        stmt_log = StatementLog(
            user_id=user_id,
            company_id=company_id,
            bank_code=bank_code,
            filename=file_path,
            original_filename=original_filename,
            status='SUCCESS',
            message='Parsed statement',
            accountno=header.get('accountno'),
            currency=header.get('currency'),
            opening_balance=header.get('openingbalance'),
            closing_balance=header.get('closingbalance'),
            details=details if details else None,
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
                user_id=user_id,
                company_id=company_id,
                bank_code=bank_code,
                filename=file_path,
                original_filename=original_filename,
                status='FAILED',
                message=str(e)
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
        filtered_details
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

        # parse transaction date to DDMMYYYY for value date (user requested)
        date_str = ''
        if tdate:
            try:
                # First try exact format produced during ingestion: 'ddmmyyyy'
                dt = pd.to_datetime(tdate, format='%d%m%Y', errors='coerce')
                if pd.isna(dt):
                    # fallback to flexible parse with dayfirst
                    dt = pd.to_datetime(tdate, dayfirst=True, errors='coerce')
                if not pd.isna(dt):
                    date_str = dt.strftime('%d%m%Y')
            except Exception:
                date_str = ''
        # If date_str still empty, fall back to statement-level min date so :61 always includes a date
        if not date_str:
            try:
                # min_date_str currently in YYMMDD; convert to DDMMYYYY fallback
                md = pd.to_datetime(min_date_str, format='%y%m%d', errors='coerce')
                date_str = md.strftime('%d%m%Y') if not pd.isna(md) else datetime.utcnow().strftime('%d%m%Y')
            except Exception:
                date_str = datetime.utcnow().strftime('%d%m%Y')
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
        line61 = f":61:{date_str}{dc_flag}{amt_str}{trx_type}{trailing}"
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
    try:
        s = str(s)
        if not s:
            return 0.0
        s = s.strip()
        if s == '':
            return 0.0
        # handle parentheses (accounting negative format)
        negative = False
        if s.startswith('(') and s.endswith(')'):
            negative = True
            s = s[1:-1]
        # remove common currency symbols, non-breaking space and normal spaces
        for ch in ['$', '€', '£', '\xa0', ' ']:
            s = s.replace(ch, '')
        # remove thousands separators commonly using comma
        s = s.replace(',', '')
        v = float(s)
        return -v if negative else v
    except Exception:
        return 0.0
