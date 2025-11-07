from models.bank_config import BankConfig
from models.bank_log import BankLog
from readers import get_reader_for_bank
from datetime import datetime

def detect_bank_and_process(session, file_path, original_filename, text, company_id=None, user_id=None):
    configs = session.query(BankConfig).filter(BankConfig.is_active == True).all()
    matched_cfg = None
    matched_keywords = []
    text_lower = text.lower()

    for cfg in configs:
        for kw in (cfg.keywords or []):
            if kw.lower() in text_lower:
                matched_cfg = cfg
                matched_keywords.append(kw)
                break
        if matched_cfg:
            break

    if not matched_cfg:
        log = BankLog(user_id=user_id,
                      company_id=company_id,
                      filename=file_path, 
                      original_filename=original_filename,
                      status="UNKNOWN", 
                      message="No matching bank",
                      processed_at=datetime.now())
        session.add(log)
        session.commit()
        return {"status": "UNKNOWN", "message": "No matching bank", "log_id": log.id}

    reader = get_reader_for_bank(matched_cfg.bank_code)
    try:
        data = reader.read(file_path, matched_cfg.scan_ranges)
        log = BankLog(user_id=user_id,
                      company_id=company_id,
                      bank_code=matched_cfg.bank_code,
                      filename=file_path,
                      original_filename=original_filename,
                      status="SUCCESS",
                      message="Processed successfully",
                      detected_keywords=matched_keywords,
                      processed_at=datetime.now())
        session.add(log)
        session.commit()
        return {"status": "SUCCESS", "bank_code": matched_cfg.bank_code, "data": data, "log_id": log.id}
    except Exception as e:
        log = BankLog(user_id=user_id,
                      company_id=company_id,
                      bank_code=matched_cfg.bank_code,
                      filename=file_path,
                      original_filename=original_filename,
                      status="FAILED",
                      message=str(e),
                      processed_at=datetime.now())
        session.add(log)
        session.commit()
        return {"status": "FAILED", "message": str(e)}