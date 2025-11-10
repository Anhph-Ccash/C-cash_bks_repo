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
    current_app.logger.info("=== START UPLOAD PROCESS ===")
    current_app.logger.info(f"Request method: {request.method}")
    current_app.logger.info(f"Request files: {request.files}")
    current_app.logger.info(f"Request form: {request.form}")
    
    f = request.files.get("file")
    if not f:
        error_msg = "No file uploaded"
        current_app.logger.error(error_msg)
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({"error": error_msg}), 400
        flash(error_msg, 'danger')
        return redirect(request.referrer or '/')

    orig_name = secure_filename(f.filename)
    current_app.logger.info(f"Original filename: {orig_name}")
    
    ext = orig_name.rsplit(".", 1)[-1].lower()
    current_app.logger.info(f"File extension: {ext}")
    current_app.logger.info(f"Allowed extensions: {current_app.config['ALLOWED_EXTENSIONS']}")
    
    if ext not in current_app.config["ALLOWED_EXTENSIONS"]:
        error_msg = f"File type '{ext}' not allowed. Allowed: {current_app.config['ALLOWED_EXTENSIONS']}"
        current_app.logger.error(error_msg)
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({"error": error_msg}), 400
        flash(error_msg, 'danger')
        return redirect(request.referrer or '/')

    os.makedirs(current_app.config["UPLOAD_FOLDER"], exist_ok=True)
    saved_name = f"{uuid.uuid4().hex}.{ext}"
    saved_path = os.path.join(current_app.config["UPLOAD_FOLDER"], saved_name)
    current_app.logger.info(f"Saving file to: {saved_path}")
    
    try:
        f.save(saved_path)
        current_app.logger.info(f"File saved successfully: {saved_path}")
    except Exception as e:
        error_msg = f"Failed to save file: {str(e)}"
        current_app.logger.error(error_msg, exc_info=True)
        flash(error_msg, 'danger')
        return redirect(request.referrer or '/')

    try:
        current_app.logger.info("Reading file to text...")
        text = read_file_to_text(saved_path, ext)
        current_app.logger.info(f"File read successfully, text length: {len(text) if text else 0}")
        
        # Get user_id and company_id from session
        user_id = session.get('user_id')
        company_id = session.get('company_id')
        current_app.logger.info(f"User ID: {user_id}, Company ID: {company_id}")
        
        current_app.logger.info("Detecting bank and processing...")
        result = detect_bank_and_process(db.session, saved_path, orig_name, text, 
                                        company_id=company_id, user_id=user_id)
        current_app.logger.info(f"Processing result: {result}")
        
        # If request comes from fetch/XHR return JSON; otherwise flash and redirect back
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(result)
        else:
            status = result.get('status', 'FAILED')
            message = result.get('message', '')
            flash(f"Upload {status}: {message}", 'success' if status == 'SUCCESS' else 'danger')
            current_app.logger.info(f"Flash message: Upload {status}: {message}")
            return redirect(request.referrer or '/')
    except Exception as e:
        db.session.rollback()
        error_msg = f"Processing error: {str(e)}"
        current_app.logger.error(error_msg, exc_info=True)
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({"status": "FAILED", "message": str(e)}), 500
        flash(f"Upload FAILED: {e}", 'danger')
        return redirect(request.referrer or '/')
    finally:
        cleanup_file(saved_path)
        current_app.logger.info("=== END UPLOAD PROCESS ===")

@upload_bp.route('/logs')
@login_required
def view_logs():
    """View all logs with filtering and pagination"""
    from models.company import Company
    import math
    
    # Get filter parameters
    bank_code = request.args.get('bank_code')
    status = request.args.get('status')
    days = request.args.get('days', type=int, default=7)
    
    # Pagination parameters
    page = request.args.get('page', type=int, default=1)
    per_page = request.args.get('per_page', type=int, default=30)
    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 30
    
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
    
    query = query.order_by(BankLog.processed_at.desc())
    
    # Calculate pagination
    total_logs = query.count()
    total_pages = max(1, math.ceil(total_logs / per_page))
    if page > total_pages:
        page = total_pages
    
    offset = (page - 1) * per_page
    logs = query.offset(offset).limit(per_page).all()
    
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total_logs,
        'total_pages': total_pages,
        'has_prev': page > 1,
        'has_next': page < total_pages,
    }
    
    return render_template('logs.html', 
                         logs=logs,
                         pagination=pagination,
                         username=session.get('username'),
                         companies=companies,
                         current_company_id=current_company_id,
                         company_name=company_name)


@upload_bp.route("/logs/delete", methods=["POST"])
@login_required
def delete_logs():
    """Delete logs based on filter criteria (admin only)"""
    
    # Check if user is admin
    user_role = session.get('role')
    if user_role != 'admin':
        flash('Chỉ admin mới được phép xóa logs!', 'error')
        return redirect(url_for('upload.view_logs'))
    
    try:
        # Get filter parameters from form
        bank_code = request.form.get('bank_code')
        status = request.form.get('status')  
        days = request.form.get('days', type=int, default=7)
        
        # Build query with same filters as view_logs
        query = BankLog.query
        
        if bank_code:
            query = query.filter(BankLog.bank_code == bank_code)
        if status:
            query = query.filter(BankLog.status == status)
        if days and days > 0:
            cutoff = datetime.now() - timedelta(days=days)
            query = query.filter(BankLog.processed_at >= cutoff)
        
        # Count logs to be deleted
        count_before = query.count()
        
        if count_before == 0:
            flash('Không tìm thấy logs nào để xóa với bộ lọc này!', 'warning')
            return redirect(url_for('upload.view_logs'))
        
        # Delete logs
        deleted_count = query.delete(synchronize_session=False)
        db.session.commit()
        
        # Log the deletion action
        current_app.logger.info(f"Admin {session.get('username')} deleted {deleted_count} logs with filters: bank_code={bank_code}, status={status}, days={days}")
        
        flash(f'✅ Đã xóa thành công {deleted_count} log(s)!', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting logs: {str(e)}")
        flash(f'❌ Lỗi khi xóa logs: {str(e)}', 'error')
    
    # Preserve filters on redirect back to logs page
    return redirect(url_for(
        'upload.view_logs',
        bank_code=bank_code or '',
        status=status or '',
        days=days if days is not None else 7
    ))