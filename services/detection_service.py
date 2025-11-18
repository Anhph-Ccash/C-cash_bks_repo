from models.bank_config import BankConfig
from models.bank_log import BankLog
from readers import get_reader_for_bank
from services.file_service import read_text_from_range
from datetime import datetime
import sys

def detect_bank_and_process(session, file_path, original_filename, text, company_id=None, user_id=None):
    """Detect bank by scanning ranges sequentially and matching keywords.

    Args:
        session: Database session
        file_path: Path to uploaded file
        original_filename: Original filename
        text: Not used anymore - kept for backward compatibility
        company_id: Company ID
        user_id: User ID

    Returns:
        Dict with status and bank detection result
    """
    print(f"[DEBUG] detect_bank_and_process called: file={original_filename}, company_id={company_id}", file=sys.stderr, flush=True)

    # Get file extension
    ext = original_filename.rsplit('.', 1)[-1] if '.' in original_filename else ''

    # Get all active bank configs
    configs = session.query(BankConfig).filter(BankConfig.is_active == True).all()
    print(f"[DEBUG] Found {len(configs)} active configs", file=sys.stderr, flush=True)

    # Collect all unique scan_ranges from all configs
    all_ranges = []
    for cfg in configs:
        if cfg.scan_ranges:
            for scan_range in cfg.scan_ranges:
                # # Avoid duplicates
                # if scan_range not in all_ranges:
                    all_ranges.append(scan_range)

    print(f"[DEBUG] Total unique scan ranges: {len(all_ranges)}", file=sys.stderr, flush=True)

    # Try each range sequentially until we find a match
    matched_cfg = None
    matched_keywords = []
    matched_range = None

    for scan_range in all_ranges:
        print(f"[DEBUG] Scanning range: {scan_range}", file=sys.stderr, flush=True)

        # Read text from this specific range
        range_text = read_text_from_range(file_path, ext, scan_range)

        if not range_text:
            print(f"[DEBUG] No text extracted from range {scan_range}", file=sys.stderr, flush=True)
            continue

        range_text_lower = range_text.lower()
        print(f"[DEBUG] Extracted text length: {len(range_text)} chars", file=sys.stderr, flush=True)

        # Check this range against all configs' keywords
        for cfg in configs:
            if not cfg.keywords:
                continue

            for kw in cfg.keywords:
                if kw.lower() in range_text_lower:
                    matched_cfg = cfg
                    matched_keywords.append(kw)
                    matched_range = scan_range
                    print(f"[DEBUG] MATCH FOUND! Bank: {cfg.bank_code}, Keyword: {kw}, Range: {scan_range}", file=sys.stderr, flush=True)
                    break

            if matched_cfg:
                break

        # If found match in this range, stop scanning
        if matched_cfg:
            break

    # No match found in any range
    if not matched_cfg:
        print(f"[DEBUG] NO MATCH FOUND in any scan range", file=sys.stderr, flush=True)
        log = BankLog(
            user_id=user_id,
            company_id=company_id,
            filename=file_path,
            original_filename=original_filename,
            status="UNKNOWN",
            message="Không tìm thấy ngân hàng phù hợp trong các vùng quét",
            processed_at=datetime.now()
        )
        session.add(log)
        session.commit()
        return {
            "status": "UNKNOWN",
            "message": "Mẫu file không hợp lệ - không tìm thấy thông tin ngân hàng trong các vùng quét",
            "log_id": log.id
        }

    # Match found - process with reader
    print(f"[DEBUG] Processing with bank_code: {matched_cfg.bank_code}", file=sys.stderr, flush=True)
    reader = get_reader_for_bank(matched_cfg.bank_code)

    try:
        data = reader.read(file_path, matched_cfg.scan_ranges)
        log = BankLog(
            user_id=user_id,
            company_id=company_id,
            bank_code=matched_cfg.bank_code,
            filename=file_path,
            original_filename=original_filename,
            status="SUCCESS",
            message=f"Phát hiện ngân hàng: {matched_cfg.bank_code} (từ vùng {matched_range})",
            processed_at=datetime.now()
        )
        session.add(log)
        session.commit()
        return {
            "status": "SUCCESS",
            "bank_code": matched_cfg.bank_code,
            "data": data,
            "log_id": log.id,
            "matched_range": matched_range,
            "matched_keywords": matched_keywords
        }
    except Exception as e:
        print(f"[DEBUG] Reader failed: {str(e)}", file=sys.stderr, flush=True)
        log = BankLog(
            user_id=user_id,
            company_id=company_id,
            bank_code=matched_cfg.bank_code,
            filename=file_path,
            original_filename=original_filename,
            status="FAILED",
            message=str(e),
            processed_at=datetime.now()
        )
        session.add(log)
        session.commit()
        return {"status": "FAILED", "message": str(e), "log_id": log.id}
