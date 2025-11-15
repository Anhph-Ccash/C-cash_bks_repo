from flask import Blueprint
bank_config_bp = Blueprint("bank_config", __name__)
from . import routes
