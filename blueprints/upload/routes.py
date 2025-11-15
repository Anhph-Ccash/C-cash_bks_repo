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
@upload_bp.route("/file", methods=["GET"])
@upload_bp.route("/admin-upload", methods=["GET"])
def admin_upload_page():
    # Show upload page with recent logs
    if 'user_id' not in session:
        return redirect('/login')

    from models.company import Company
    from models.statement_log import StatementLog

    # Get all companies for admin
    companies = Company.query.filter_by(is_active=True).all()
    current_company_id = session.get('company_id')
    company_name = session.get('company_name')

    recent_logs = BankLog.query.order_by(
        BankLog.processed_at.desc()
    ).limit(10).all()

    # Get recent statement logs (parsed statements)
    statement_logs = StatementLog.query.order_by(
        StatementLog.processed_at.desc()
    ).limit(10).all()

    return render_template('admin_upload.html',
                         username=session.get('username'),
                         logs=recent_logs,
                         statement_logs=statement_logs,
                         companies=companies,
                         current_company_id=current_company_id,
                         company_name=company_name)

@upload_bp.route("/file", methods=["POST"])
@upload_bp.route("/admin-upload", methods=["POST"])
def process_upload():
    """Upload file for admin - includes ZIP processing and MT940 generation"""
    import shutil
    from services.zip_service import safe_extract_zip
    from services.statement_service import parse_and_store_statement
    from models.statement_log import StatementLog

    user_id = session.get('user_id')
    company_id = session.get('company_id')

    # Validate user exists
    from models import User
    user = User.query.get(user_id)
    if not user:
        flash("User không tồn tại, vui lòng đăng nhập lại!", 'danger')
        return redirect(url_for('auth.logout'))

    if not company_id:
        flash("Vui lòng chọn công ty trước khi upload!", 'warning')
        return redirect(url_for('upload.admin_upload_page'))

    f = request.files.get("file")
    if not f:
        flash("Không tìm thấy file!", 'danger')
        return redirect(url_for('upload.admin_upload_page'))

    orig_name = secure_filename(f.filename)
    ext = orig_name.rsplit(".", 1)[-1].lower()
    if ext not in current_app.config["ALLOWED_EXTENSIONS"]:
        flash("Định dạng file không được hỗ trợ!", 'danger')
        return redirect(url_for('upload.admin_upload_page'))

    os.makedirs(current_app.config["UPLOAD_FOLDER"], exist_ok=True)
    saved_name = f"{uuid.uuid4().hex}.{ext}"
    saved_path = os.path.join(current_app.config["UPLOAD_FOLDER"], saved_name)
    f.save(saved_path)

    # track first parsed statement that is missing an account number so we can redirect
    missing_statement_log_id = None

    try:
        # If uploaded file is a ZIP archive, extract and process each allowed file inside
        if ext == 'zip':
            temp_dir = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), 'tmp', uuid.uuid4().hex)
            os.makedirs(temp_dir, exist_ok=True)
            # allowed extensions inside zip (exclude zip itself)
            allowed = set(current_app.config.get('ALLOWED_EXTENSIONS', set())) - {'zip'}
            extracted = safe_extract_zip(saved_path, temp_dir, allowed_exts=allowed)
            processed = 0
            successes = 0
            failures = []
            for ef in extracted:
                try:
                    orig_inner = os.path.basename(ef)
                    inner_ext = orig_inner.rsplit('.', 1)[-1].lower() if '.' in orig_inner else ''
                    text = read_file_to_text(ef, inner_ext)
                    result = detect_bank_and_process(db.session, ef, orig_inner, text, company_id, user_id)
                    status = result.get('status', 'FAILED')
                    processed += 1
                    if status == 'SUCCESS' and result.get('bank_code'):
                        parse_result = parse_and_store_statement(db.session, ef, orig_inner, inner_ext, company_id, result.get('bank_code'), user_id)

                        if parse_result.get('status') == 'INVALID':
                            # Validation failed
                            failures.append(f"{orig_inner}: {parse_result.get('message', 'Không hợp lệ')}")
                        elif parse_result.get('status') == 'SUCCESS':
                            successes += 1
                            # if the parsed statement was created but account is missing, remember it
                            sid = parse_result.get('statement_log_id')
                            if sid and missing_statement_log_id is None:
                                try:
                                    stmt = StatementLog.query.filter_by(id=sid).first()
                                    if stmt and not (stmt.accountno and str(stmt.accountno).strip()):
                                        missing_statement_log_id = sid
                                except Exception:
                                    pass
                        else:
                            failures.append((orig_inner, parse_result.get('message')))
                    else:
                        failures.append((orig_inner, result.get('message') or 'Detection failed'))
                except Exception as e:
                    failures.append((ef, str(e)))

            # cleanup extracted files
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass

            # flash summary
            flash(f"ZIP processed: {processed} files, successes: {successes}, failures: {len(failures)}", 'success' if successes>0 else 'warning')
            for fn, msg in failures[:5]:
                flash(f"{fn}: {msg}", 'warning')

        else:
            text = read_file_to_text(saved_path, ext)
            result = detect_bank_and_process(db.session, saved_path, orig_name, text, company_id, user_id)
            status = result.get('status', 'FAILED')
            message = result.get('message', '')
            flash(f"Upload {status}: {message}", 'success' if status == 'SUCCESS' else 'danger')

            # If detection succeeded, attempt to parse statement configs and create MT940
            if status == 'SUCCESS' and result.get('bank_code'):
                try:
                    ext_for_parse = ext
                    parse_result = parse_and_store_statement(db.session, saved_path, orig_name, ext_for_parse, company_id, result.get('bank_code'), user_id)

                    if parse_result.get('status') == 'INVALID':
                        # Validation failed - show detailed errors
                        errors = parse_result.get('errors', [])
                        error_msg = parse_result.get('message', 'Mẫu sổ phụ không hợp lệ')
                        flash(error_msg, 'danger')
                        for err in errors[:5]:  # Show first 5 errors
                            flash(f"• {err}", 'warning')
                    elif parse_result.get('status') == 'SUCCESS':
                        flash('Sổ phụ đã được phân tích và MT940 sẵn sàng để tải xuống.', 'success')
                        # if account missing on the created StatementLog, redirect to edit it
                        sid = parse_result.get('statement_log_id')
                        if sid:
                            try:
                                stmt = StatementLog.query.filter_by(id=sid).first()
                                if stmt and not (stmt.accountno and str(stmt.accountno).strip()):
                                    # cleanup saved file before redirect
                                    cleanup_file(saved_path)
                                    return redirect(url_for('main.view_statement_detail', log_id=sid))
                            except Exception:
                                # ignore and continue
                                pass
                    else:
                        flash(f"Phân tích sổ phụ thất bại: {parse_result.get('message')}", 'warning')
                except Exception as e:
                    db.session.rollback()
                    flash(f"Lỗi khi phân tích sổ phụ: {e}", 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f"Upload FAILED: {e}", 'danger')
    finally:
        cleanup_file(saved_path)

    # If any parsed statement was missing account number, redirect to the first such statement
    if missing_statement_log_id:
        return redirect(url_for('main.view_statement_detail', log_id=missing_statement_log_id))

    return redirect(url_for('upload.admin_upload_page'))

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


@upload_bp.route("/statement-logs")
@login_required
def list_statement_logs():
    """List all statement logs with filters and pagination"""
    from models.company import Company
    from models.statement_log import StatementLog
    import math

    # Get filter parameters
    bank_code = request.args.get('bank_code')
    status = request.args.get('status')
    date_from = request.args.get('from')
    date_to = request.args.get('to')

    # Base query
    user_id = session.get('user_id')
    query = StatementLog.query.filter(StatementLog.user_id == user_id)

    # Admin can see all statement logs or company-wide
    if session.get('role') == 'admin':
        query = StatementLog.query

    # Filter by company if set
    company_id = session.get('company_id')
    if company_id:
        query = query.filter(StatementLog.company_id == company_id)

    # Apply filters
    if bank_code:
        query = query.filter(StatementLog.bank_code == bank_code)
    if status:
        query = query.filter(StatementLog.status == status)

    # Date range filters
    if date_from:
        try:
            df = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(StatementLog.processed_at >= df)
        except Exception:
            pass
    if date_to:
        try:
            dt = datetime.strptime(date_to, '%Y-%m-%d')
            # Add one day to include the entire "to" date
            dt = dt + timedelta(days=1)
            query = query.filter(StatementLog.processed_at < dt)
        except Exception:
            pass

    # Pagination
    page = request.args.get('page', type=int, default=1)
    per_page = request.args.get('per_page', type=int, default=30)
    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 30

    total = query.count()
    total_pages = max(1, math.ceil(total / per_page))
    if page > total_pages:
        page = total_pages

    offset = (page - 1) * per_page
    logs = query.order_by(StatementLog.processed_at.desc()).offset(offset).limit(per_page).all()

    # Get distinct bank codes for filter dropdown
    banks = [r[0] for r in db.session.query(StatementLog.bank_code).distinct().all() if r[0]]

    # Get companies for navbar
    companies = Company.query.filter_by(is_active=True).all()
    current_company_id = session.get('company_id')
    company_name = session.get('company_name')

    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': total_pages,
        'has_prev': page > 1,
        'has_next': page < total_pages,
    }

    return render_template('statement_logs.html',
                         logs=logs,
                         banks=banks,
                         username=session.get('username'),
                         pagination=pagination,
                         companies=companies,
                         current_company_id=current_company_id,
                         company_name=company_name)
