from flask import jsonify
from models import BankLog
from . import bank_log_bp

@bank_log_bp.route("/", methods=["GET"])
def list_logs():
    logs = BankLog.query.order_by(BankLog.id.desc()).limit(20).all()
    return jsonify([{
        "id": l.id,
        "bank_code": l.bank_code,
        "status": l.status,
        "message": l.message,
        "filename": l.original_filename,
        "processed_at": str(l.processed_at)
    } for l in logs])
