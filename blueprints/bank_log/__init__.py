from flask import Blueprint
bank_log_bp = Blueprint("bank_log", __name__)
from . import routes
