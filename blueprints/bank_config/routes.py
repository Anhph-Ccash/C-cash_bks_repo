from flask import jsonify, request
from extensions import db
from models import BankConfig
from . import bank_config_bp

@bank_config_bp.route("/", methods=["GET"])
def list_config():
    # Return configs ordered by bank_code A-Z for predictability
    configs = BankConfig.query.order_by(BankConfig.bank_code.asc()).all()
    return jsonify([{
        "bank_code": c.bank_code,
        "keywords": c.keywords,
        "scan_ranges": c.scan_ranges
    } for c in configs])