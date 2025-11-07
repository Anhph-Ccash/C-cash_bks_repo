import os, uuid
from flask import current_app, request, jsonify, render_template, flash, redirect, session, url_for
from werkzeug.utils import secure_filename
from extensions import db
from services.file_service import read_file_to_text, cleanup_file
from services.detection_service import detect_bank_and_process
from models.bank_log import BankLog
from datetime import datetime, timedelta
from functools import wraps

from . import upload_bp

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@upload_bp.route("/", methods=["GET"])
@upload_bp.route("/upload", methods=["GET"])
def upload_file():
    # Show upload page with recent logs
    if 'user_id' not in session:
        return redirect('/login')
    
    from models.company import Company
    
    # Get all companies for admin
    companies = Company.query.filter_by(is_active=True).all()
    current_company_id = session.get('company_id')
    company_name = session.get('company_name')
    
    recent_logs = BankLog.query.order_by(
        BankLog.processed_at.desc()
    ).limit(10).all()
    
    return render_template('upload.html', 
                         username=session.get('username'),
                         logs=recent_logs,
                         companies=companies,
                         current_company_id=current_company_id,
                         company_name=company_name)

@upload_bp.route("/file", methods=["POST"])
@upload_bp.route("/upload", methods=["POST"])
def process_upload():
    f = request.files.get("file")
    if not f:
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({"error": "no file uploaded"}), 400
        flash("No file uploaded", 'danger')
        return redirect(request.referrer or '/')

    orig_name = secure_filename(f.filename)
    ext = orig_name.rsplit(".", 1)[-1].lower()
    if ext not in current_app.config["ALLOWED_EXTENSIONS"]:
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({"error": "file type not allowed"}), 400
        flash("File type not allowed", 'danger')
        return redirect(request.referrer or '/')

    os.makedirs(current_app.config["UPLOAD_FOLDER"], exist_ok=True)
    saved_name = f"{uuid.uuid4().hex}.{ext}"
    saved_path = os.path.join(current_app.config["UPLOAD_FOLDER"], saved_name)
    f.save(saved_path)

    try:
        text = read_file_to_text(saved_path, ext)
        result = detect_bank_and_process(db.session, saved_path, orig_name, text)
        # If request comes from fetch/XHR return JSON; otherwise flash and redirect back
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(result)
        else:
            status = result.get('status', 'FAILED')
            message = result.get('message', '')
            flash(f"Upload {status}: {message}", 'success' if status == 'SUCCESS' else 'danger')
            return redirect(request.referrer or '/')
    except Exception as e:
        db.session.rollback()
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({"status": "FAILED", "message": str(e)}), 500
        flash(f"Upload FAILED: {e}", 'danger')
        return redirect(request.referrer or '/')
    finally:
        cleanup_file(saved_path)

@upload_bp.route('/logs')
@login_required
def view_logs():
    """View all logs with filtering"""
    from models.company import Company
    
    # Get filter parameters
    bank_code = request.args.get('bank_code')
    status = request.args.get('status')
    days = request.args.get('days', type=int, default=7)
    
    # Get all companies for admin
    companies = Company.query.filter_by(is_active=True).all()
    current_company_id = session.get('company_id')
    company_name = session.get('company_name')
    
    query = BankLog.query
    
    if bank_code:
        query = query.filter(BankLog.bank_code == bank_code)
    if status:
        query = query.filter(BankLog.status == status)
    if days and days > 0:
        cutoff = datetime.now() - timedelta(days=days)
        query = query.filter(BankLog.processed_at >= cutoff)
        
    logs = query.order_by(BankLog.processed_at.desc()).all()
    
    return render_template('logs.html', 
                         logs=logs,
                         username=session.get('username'),
                         companies=companies,
                         current_company_id=current_company_id,
                         company_name=company_name)