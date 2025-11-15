import uuid
from flask import Blueprint, render_template, redirect, url_for, session, request, flash
from werkzeug.utils import secure_filename
from functools import wraps
import os
from extensions import db
from models.bank_log import BankLog
from services.file_service import read_file_to_text, cleanup_file
from services.zip_service import safe_extract_zip
import shutil
from services.detection_service import detect_bank_and_process
from services.statement_service import parse_and_store_statement
from models.statement_log import StatementLog
from flask import send_file, abort
from datetime import datetime, timedelta
from flask import current_app
from sqlalchemy import and_

main_bp = Blueprint('main', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def user_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        if session.get('role') == 'admin':
            flash('Admin vui lòng sử dụng Admin Panel', 'warning')
            return redirect(url_for('admin.admin'))
        return f(*args, **kwargs)
    return decorated_function

@main_bp.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    # Redirect based on role
    if session.get('role') == 'admin':
        return redirect(url_for('admin.admin'))
    else:
        return redirect(url_for('main.user_dashboard'))

@main_bp.route('/dashboard')
@user_required
def user_dashboard():
    from models import User, Company
    from models.bank_config import BankConfig

    # Get user's companies
    user = User.query.get(session['user_id'])
    companies = user.get_companies()

    # Get current company_id from session
    company_id = session.get('company_id')

    # Get recent logs for the dashboard filtered by user and company
    query = BankLog.query.filter(BankLog.user_id == session['user_id'])
    if company_id:
        query = query.filter(BankLog.company_id == company_id)

    recent_logs = query.order_by(
        BankLog.processed_at.desc()
    ).limit(10).all()

    # Attach MT940 availability info to recent logs by matching filenames to StatementLog
    try:
        for log in recent_logs:
            # default attributes
            setattr(log, 'mt940_available', False)
            setattr(log, 'mt940_log_id', None)
            setattr(log, 'mt940_filename', None)

            # match by filename (both BankLog and StatementLog store the saved file path)
            if getattr(log, 'filename', None):
                stmt = StatementLog.query.filter(StatementLog.filename == log.filename)
                # restrict by user/company when available to avoid exposing other users' files
                if session.get('user_id'):
                    stmt = stmt.filter(StatementLog.user_id == session.get('user_id'))
                if company_id:
                    stmt = stmt.filter(StatementLog.company_id == company_id)
                stmt = stmt.first()
                if stmt and stmt.mt940_filename:
                    setattr(log, 'mt940_available', True)
                    setattr(log, 'mt940_log_id', stmt.id)
                    setattr(log, 'mt940_filename', stmt.mt940_filename)
    except Exception:
        # non-fatal: if something goes wrong here, don't block the dashboard
        pass

    # Get bank configs for current company
    bank_configs = []
    statement_configs = []
    if company_id:
        # Order bank configs alphabetically by bank_code (A-Z)
        bank_configs = BankConfig.query.filter_by(
            company_id=company_id,
            is_active=True
        ).order_by(BankConfig.bank_code.asc()).all()

        # Get statement configs
        from models.bank_statement_config import BankStatementConfig
        # Order statement configs by bank_code alphabetically
        statement_configs = BankStatementConfig.query.filter_by(
            company_id=company_id
        ).order_by(BankStatementConfig.bank_code.asc()).all()

    # Recent parsed statements
    stmt_query = None
    stmt_query = StatementLog.query.filter(StatementLog.user_id == session['user_id'])
    if company_id:
        stmt_query = stmt_query.filter(StatementLog.company_id == company_id)
    statement_logs = stmt_query.order_by(StatementLog.processed_at.desc()).limit(10).all()

    return render_template('users.html',
                         username=session.get('username'),
                         company_name=session.get('company_name'),
                         companies=companies,
                         current_company_id=company_id,
                         logs=recent_logs,
                         statement_logs=statement_logs,
                         bank_configs=bank_configs,
                         statement_configs=statement_configs)


@main_bp.route('/user/user-upload-page')
@login_required
def user_upload_page():
    """User upload page with recent logs and statement logs"""
    from models import User, Company

    user_id = session.get('user_id')
    user = User.query.get(user_id)
    if not user:
        flash("User không tồn tại!", 'danger')
        return redirect(url_for('auth.logout'))

    # Get user's companies
    companies = user.get_companies()
    company_id = session.get('company_id')
    company_name = session.get('company_name')

    # Get recent bank logs
    recent_logs = BankLog.query.filter_by(user_id=user_id).order_by(
        BankLog.processed_at.desc()
    ).limit(10).all()

    # Get recent statement logs (parsed statements)
    statement_logs = StatementLog.query.filter_by(user_id=user_id).order_by(
        StatementLog.processed_at.desc()
    ).limit(10).all()

    return render_template('user_upload.html',
                         username=user.username,
                         logs=recent_logs,
                         statement_logs=statement_logs,
                         companies=companies,
                         current_company_id=company_id,
                         company_name=company_name)


@main_bp.route('/bank-configs')
@login_required
def user_bank_configs():
    """Redirect to admin bank configs page"""
    if session.get('role') != 'admin':
        flash('Chỉ Admin mới có quyền truy cập trang này!', 'danger')
        return redirect(url_for('main.user_dashboard'))

    # Redirect to admin route
    return redirect(url_for('admin.manage_bank_configs'))


@main_bp.route('/user/upload', methods=['POST'])
@user_required
def user_upload():
    """Upload file for regular users"""
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
        return redirect(url_for('main.user_dashboard'))

    f = request.files.get("file")
    if not f:
        flash("Không tìm thấy file!", 'danger')
        return redirect(url_for('main.user_dashboard'))

    orig_name = secure_filename(f.filename)
    ext = orig_name.rsplit(".", 1)[-1].lower()
    if ext not in current_app.config["ALLOWED_EXTENSIONS"]:
        flash("Định dạng file không được hỗ trợ!", 'danger')
        return redirect(url_for('main.user_dashboard'))

    os.makedirs(current_app.config["UPLOAD_FOLDER"], exist_ok=True)
    saved_name = f"{uuid.uuid4().hex}.{ext}"
    saved_path = os.path.join(current_app.config["UPLOAD_FOLDER"], saved_name)
    f.save(saved_path)
    # track first parsed statement that is missing an account number so we can redirect
    missing_statement_log_id = None

    try:
        user_id = session.get('user_id')

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
                        # if account missing on the created StatementLog, redirect user to edit it
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

    # If any parsed statement was missing account number, redirect the user to the first such statement
    if missing_statement_log_id:
        return redirect(url_for('main.view_statement_detail', log_id=missing_statement_log_id))

    return redirect(url_for('main.user_dashboard'))

@main_bp.route('/user/logs')
@user_required
def user_logs():
    """View logs for regular users"""
    from models import User
    import math

    bank_code = request.args.get('bank_code')
    status = request.args.get('status')
    days = request.args.get('days', type=int, default=7)
    page = request.args.get('page', type=int, default=1)
    per_page = request.args.get('per_page', type=int, default=10)
    if not per_page or per_page < 1:
        per_page = 10
    if not page or page < 1:
        page = 1

    # Get user's companies
    user = User.query.get(session['user_id'])
    companies = user.get_companies()
    company_id = session.get('company_id')

    # Filter by user first - only show logs uploaded by this user
    query = BankLog.query.filter(BankLog.user_id == session['user_id'])

    # Filter by company
    if company_id:
        query = query.filter(BankLog.company_id == company_id)

    if bank_code:
        query = query.filter(BankLog.bank_code == bank_code)
    if status:
        query = query.filter(BankLog.status == status)
    if days and days > 0:
        cutoff = datetime.now() - timedelta(days=days)
        query = query.filter(BankLog.processed_at >= cutoff)

    total = query.count()
    total_pages = max(1, math.ceil(total / per_page))
    if page > total_pages:
        page = total_pages
    offset = (page - 1) * per_page
    logs = query.order_by(BankLog.processed_at.desc()).offset(offset).limit(per_page).all()

    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': total_pages,
        'has_prev': page > 1,
        'has_next': page < total_pages,
    }

    return render_template('user_logs.html',
                         logs=logs,
                         username=session.get('username'),
                         company_name=session.get('company_name'),
                         companies=companies,
                         current_company_id=company_id,
                         pagination=pagination)


@main_bp.route('/user/logs/bulk-delete', methods=['POST'])
@user_required
def user_logs_bulk_delete():
    """Bulk delete selected BankLog entries for the current user (and company if selected)."""
    ids = request.form.getlist('ids')
    if not ids:
        flash('Vui lòng chọn ít nhất một bản ghi để xóa.', 'warning')
        return redirect(url_for('main.user_logs'))

    try:
        # sanitize ids to integers
        id_list = []
        for _id in ids:
            try:
                id_list.append(int(_id))
            except Exception:
                continue
        if not id_list:
            flash('Danh sách lựa chọn không hợp lệ.', 'warning')
            return redirect(url_for('main.user_logs'))

        # enforce ownership: only delete logs created by this user (and current company if any)
        q = BankLog.query.filter(BankLog.user_id == session['user_id'], BankLog.id.in_(id_list))
        if session.get('company_id'):
            q = q.filter(BankLog.company_id == session.get('company_id'))

        to_delete = q.all()
        count = len(to_delete)
        if count == 0:
            flash('Không tìm thấy bản ghi hợp lệ để xóa.', 'warning')
            return redirect(url_for('main.user_logs'))

        for item in to_delete:
            db.session.delete(item)
        db.session.commit()
        flash(f'Đã xóa {count} bản ghi lịch sử tải lên.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Xóa thất bại: {e}', 'danger')

    return redirect(url_for('main.user_logs'))


@main_bp.route('/user/statement-logs')
@user_required
def list_statement_logs():
    """List all statement logs for the user with simple filters."""
    from models import Company
    import math

    bank_code = request.args.get('bank_code')
    status = request.args.get('status')
    date_from = request.args.get('from')
    date_to = request.args.get('to')

    query = StatementLog.query.filter(StatementLog.user_id == session['user_id'])
    if session.get('role') == 'admin':
        # admin can see company-wide (optional behavior)
        query = StatementLog.query

    company_id = session.get('company_id')
    if company_id:
        query = query.filter(StatementLog.company_id == company_id)

    if bank_code:
        query = query.filter(StatementLog.bank_code == bank_code)
    if status:
        query = query.filter(StatementLog.status == status)

    # simple date filters
    if date_from:
        try:
            df = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(StatementLog.processed_at >= df)
        except Exception:
            pass
    if date_to:
        try:
            dt = datetime.strptime(date_to, '%Y-%m-%d')
            query = query.filter(StatementLog.processed_at <= dt)
        except Exception:
            pass

    # Pagination
    page = request.args.get('page', type=int, default=1)
    per_page = request.args.get('per_page', type=int, default=10)
    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 10

    total = query.count()
    total_pages = max(1, math.ceil(total / per_page))
    if page > total_pages:
        page = total_pages

    offset = (page - 1) * per_page
    logs = query.order_by(StatementLog.processed_at.desc()).offset(offset).limit(per_page).all()

    # distinct bank codes for filter dropdown
    banks = [r[0] for r in db.session.query(StatementLog.bank_code).distinct().all()]

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


@main_bp.route('/user/bank-log/<int:log_id>/download')
@login_required
def download_bank_log_file(log_id):
    """Download the original uploaded Excel/CSV file from BankLog.
    Permission: admin OR owner user OR same-company user.
    """
    print(f"[DEBUG] Attempting to download bank log ID: {log_id}")
    print(f"[DEBUG] Current user_id in session: {session.get('user_id')}")

    log = BankLog.query.filter_by(id=log_id).first()
    if not log:
        print(f"[DEBUG] Log ID {log_id} does not exist in database")
        abort(404)

    # permission: owner, company, or admin
    allowed = False
    if session.get('role') == 'admin':
        allowed = True
    elif log.user_id and log.user_id == session.get('user_id'):
        allowed = True
    elif log.company_id and log.company_id == session.get('company_id'):
        allowed = True

    if not allowed:
        print(f"[DEBUG] Permission denied for user {session.get('user_id')} on bank log {log_id}")
        # Role-aware redirect
        flash('Bạn không có quyền tải file này.', 'danger')
        if session.get('role') == 'admin':
            return redirect(url_for('admin.admin_view_logs'))
        return redirect(url_for('main.user_logs'))

    print(f"[DEBUG] Found log - filename: {log.filename}, original_filename: {log.original_filename}")

    if not log.filename:
        print(f"[DEBUG] Log has no filename")
        abort(404)

    full_path = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), log.filename)
    print(f"[DEBUG] Full path to file: {full_path}")
    print(f"[DEBUG] File exists: {os.path.exists(full_path)}")

    if not os.path.exists(full_path):
        print(f"[DEBUG] File not found at path: {full_path}")
        abort(404)

    # Use original filename for download
    download_name = log.original_filename if log.original_filename else os.path.basename(log.filename)
    print(f"[DEBUG] Sending file with download name: {download_name}")
    return send_file(full_path, as_attachment=True, download_name=download_name)


@main_bp.route('/user/statement-log/<int:log_id>/download')
@login_required
def download_statement_mt940(log_id):
    """Allow both user and admin to download generated MT940 for a statement log.
    Permission: owner user OR same company OR admin.
    """
    stmt = StatementLog.query.filter_by(id=log_id).first()
    if not stmt or not stmt.mt940_filename:
        abort(404)

    # permission: owner, company, or admin
    allowed = False
    if session.get('role') == 'admin':
        allowed = True
    elif stmt.user_id and stmt.user_id == session.get('user_id'):
        allowed = True
    elif stmt.company_id and stmt.company_id == session.get('company_id'):
        allowed = True

    if not allowed:
        # If not permitted, redirect appropriately per role
        flash('Bạn không có quyền tải file MT940 này.', 'danger')
        if session.get('role') == 'admin':
            return redirect(url_for('admin.admin_upload_page'))
        return redirect(url_for('main.user_dashboard'))

    full_path = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), stmt.mt940_filename)
    if not os.path.exists(full_path):
        abort(404)

    # Provide a friendly download name if available
    download_name = os.path.basename(stmt.mt940_filename)
    return send_file(full_path, as_attachment=True, download_name=download_name)


@main_bp.route('/user/statement-log/<int:log_id>')
@login_required
def view_statement_detail(log_id):
    """Show parsed statement header and details.
    Allow admin, owner user, or same-company user to view.
    """
    stmt = StatementLog.query.filter_by(id=log_id).first()
    if not stmt:
        abort(404)

    # permission: owner, company, or admin
    allowed = False
    if session.get('role') == 'admin':
        allowed = True
    elif stmt.user_id and stmt.user_id == session.get('user_id'):
        allowed = True
    elif stmt.company_id and stmt.company_id == session.get('company_id'):
        allowed = True

    if not allowed:
        flash('Bạn không có quyền xem chi tiết bản ghi này.', 'danger')
        if session.get('role') == 'admin':
            return redirect(url_for('admin.admin_upload_page'))
        return redirect(url_for('main.user_dashboard'))

    # details is stored as JSON list of dicts
    details = stmt.details or []

    return render_template('statement_detail.html', stmt=stmt, details=details, username=session.get('username'), company_name=session.get('company_name'))


@main_bp.route('/user/statement-log/<int:log_id>/update-account', methods=['POST'])
@user_required
def update_statement_account(log_id):
    """Allow user to update account number for a parsed statement and (re)generate MT940."""
    from services.statement_service import build_mt940_strict
    stmt = StatementLog.query.filter_by(id=log_id).first()
    if not stmt:
        flash('Không tìm thấy bản ghi.', 'danger')
        return redirect(url_for('main.user_dashboard'))

    # permission: owner, company, or admin
    allowed = False
    if session.get('role') == 'admin':
        allowed = True
    elif stmt.user_id and stmt.user_id == session.get('user_id'):
        allowed = True
    elif stmt.company_id and stmt.company_id == session.get('company_id'):
        allowed = True

    if not allowed:
        flash('Bạn không có quyền cập nhật.', 'danger')
        return redirect(url_for('main.user_dashboard'))

    new_acc = request.form.get('accountno', '').strip()
    if not new_acc:
        flash('Vui lòng nhập số tài khoản hợp lệ.', 'warning')
        return redirect(url_for('main.view_statement_detail', log_id=log_id))

    try:
        stmt.accountno = new_acc
        # remove old mt940 file if exists
        if stmt.mt940_filename:
            try:
                old_path = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), stmt.mt940_filename)
                if os.path.exists(old_path):
                    os.remove(old_path)
            except Exception:
                pass

        # regenerate mt940 and write file
        mt_text = build_mt940_strict(stmt)
        mt_dir = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), 'mt940')
        os.makedirs(mt_dir, exist_ok=True)
        ts = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        safe_name = (stmt.original_filename or 'statement').rsplit('.', 1)[0]
        mt_filename = f"{safe_name}_{stmt.bank_code}_{ts}.mt940.txt"
        mt_path = os.path.join(mt_dir, mt_filename)
        with open(mt_path, 'w', encoding='utf-8') as f:
            f.write(mt_text)

        rel_path = os.path.relpath(mt_path, current_app.config.get('UPLOAD_FOLDER', 'uploads'))
        stmt.mt940_filename = rel_path.replace('\\', '/')
        stmt.status = 'SUCCESS'
        stmt.message = 'MT940 generated after account update'
        db.session.commit()
        flash('Đã cập nhật số tài khoản và sinh MT940 thành công.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Lỗi khi cập nhật: {e}', 'danger')

    return redirect(url_for('main.view_statement_detail', log_id=log_id))


@main_bp.route('/user/statement-log/delete/<int:log_id>')
@login_required
def delete_statement_log(log_id):
    """Delete a StatementLog record and associated MT940 file (if present)."""
    stmt = StatementLog.query.filter_by(id=log_id).first()
    if not stmt:
        flash('Không tìm thấy bản ghi.', 'danger')
        return redirect(url_for('main.user_dashboard'))

    # Only allow owner, company owner, or admin to delete
    allowed = False
    if session.get('role') == 'admin':
        allowed = True
    elif stmt.user_id and stmt.user_id == session.get('user_id'):
        allowed = True
    elif stmt.company_id and stmt.company_id == session.get('company_id'):
        allowed = True

    if not allowed:
        flash('Bạn không có quyền xóa bản ghi này.', 'danger')
        return redirect(url_for('main.user_dashboard'))

    # attempt to remove mt940 file if exists
    try:
        if stmt.mt940_filename:
            mt_path = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), stmt.mt940_filename)
            if os.path.exists(mt_path):
                os.remove(mt_path)
    except Exception:
        # ignore file delete errors
        pass

    try:
        db.session.delete(stmt)
        db.session.commit()
        flash('Đã xóa bản ghi sổ phụ.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Lỗi khi xóa bản ghi: {e}', 'danger')

    # Redirect based on user role and referrer
    # If admin, redirect to admin upload page; otherwise user dashboard
    if session.get('role') == 'admin':
        # Check for 'next' parameter first (highest priority)
        next_page = request.args.get('next')
        if next_page:
            current_app.logger.info(f"[DEBUG] Delete statement_log - Using next parameter: {next_page}")
            return redirect(next_page)

        # Check referrer
        referrer = request.referrer or ''
        current_app.logger.info(f"[DEBUG] Delete statement_log - Referrer: {referrer}")

        if 'statement-logs' in referrer or 'statement_logs' in referrer:
            current_app.logger.info("[DEBUG] Redirecting to statement_logs")
            return redirect(url_for('upload.list_statement_logs'))
        elif 'admin-upload' in referrer or 'admin/upload/admin-upload' in referrer or 'upload/admin/admin-upload' in referrer:
            current_app.logger.info("[DEBUG] Redirecting to admin_upload_page")
            return redirect(url_for('admin.admin_upload_page'))
        elif 'users' in referrer or 'admin-users' in referrer:
            current_app.logger.info("[DEBUG] Redirecting to manage_users")
            return redirect(url_for('admin.manage_users'))
        else:
            # Default to admin upload page
            current_app.logger.info("[DEBUG] Default redirect to admin_upload_page")
            return redirect(url_for('admin.admin_upload_page'))
    else:
        return redirect(url_for('main.user_dashboard'))

@main_bp.route('/user/bank-config/add', methods=['POST'])
@login_required
def add_bank_config():
    """Admin-only: Add bank config for company"""
    if session.get('role') != 'admin':
        flash('Chỉ Admin mới có quyền thực hiện thao tác này!', 'danger')
        return redirect(url_for('admin.manage_bank_configs'))

    from models.bank_config import BankConfig

    company_id = session.get('company_id')
    if not company_id:
        flash("⚠️ Vui lòng chọn công ty trước khi thêm cấu hình ngân hàng!", 'warning')
        return redirect(url_for('admin.manage_bank_configs'))

    try:
        bank_code = request.form.get('bank_code', '').strip().upper()
        bank_name = request.form.get('bank_name', '').strip()
        keywords = request.form.get('keywords', '').strip()

        # Validation
        if not bank_code:
            flash("❌ Mã ngân hàng không được để trống!", 'danger')
            return redirect(url_for('admin.manage_bank_configs'))

        if not keywords:
            flash("❌ Từ khóa không được để trống!", 'danger')
            return redirect(url_for('admin.manage_bank_configs'))

        # Check if bank_code already exists for this company
        existing = BankConfig.query.filter_by(
            company_id=company_id,
            bank_code=bank_code
        ).first()

        if existing:
            flash(f"❌ Mã ngân hàng '{bank_code}' đã tồn tại trong công ty này!", 'danger')
            return redirect(url_for('admin.manage_bank_configs'))

        # Convert keywords string to array
        keywords_array = [kw.strip() for kw in keywords.split(',') if kw.strip()]

        if not keywords_array:
            flash("❌ Vui lòng nhập ít nhất một từ khóa hợp lệ!", 'danger')
            return redirect(url_for('admin.manage_bank_configs'))

        config = BankConfig(
            company_id=company_id,
            bank_code=bank_code,
            bank_name=bank_name if bank_name else None,
            keywords=keywords_array,
            scan_ranges=[],
            is_active=True
        )
        db.session.add(config)
        db.session.commit()
        flash(f"✅ Đã thêm cấu hình ngân hàng {bank_code} thành công!", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"❌ Lỗi khi thêm cấu hình: {str(e)}", 'danger')

    return redirect(url_for('admin.manage_bank_configs'))

@main_bp.route('/user/bank-config/update/<int:config_id>', methods=['POST'])
@login_required
def update_bank_config(config_id):
    """Admin-only: Update bank config"""
    if session.get('role') != 'admin':
        flash('Chỉ Admin mới có quyền thực hiện thao tác này!', 'danger')
        return redirect(url_for('admin.manage_bank_configs'))

    from models.bank_config import BankConfig

    company_id = session.get('company_id')
    config = BankConfig.query.filter_by(id=config_id, company_id=company_id).first()

    if not config:
        flash("❌ Không tìm thấy cấu hình hoặc bạn không có quyền!", 'danger')
        return redirect(url_for('admin.manage_bank_configs'))

    try:
        bank_code = request.form.get('bank_code', '').strip().upper()
        bank_name = request.form.get('bank_name', '').strip()
        keywords = request.form.get('keywords', '').strip()

        # Validation
        if not bank_code:
            flash("❌ Mã ngân hàng không được để trống!", 'danger')
            return redirect(url_for('admin.manage_bank_configs'))

        if not keywords:
            flash("❌ Từ khóa không được để trống!", 'danger')
            return redirect(url_for('admin.manage_bank_configs'))

        # Convert keywords string to array
        keywords_array = [kw.strip() for kw in keywords.split(',') if kw.strip()]

        if not keywords_array:
            flash("❌ Vui lòng nhập ít nhất một từ khóa hợp lệ!", 'danger')
            return redirect(url_for('admin.manage_bank_configs'))

        config.bank_code = bank_code
        config.bank_name = bank_name if bank_name else None
        config.keywords = keywords_array
        db.session.commit()
        flash(f"✅ Đã cập nhật cấu hình {bank_code} thành công!", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"❌ Lỗi khi cập nhật: {str(e)}", 'danger')

    return redirect(url_for('admin.manage_bank_configs'))

@main_bp.route('/user/bank-config/delete/<int:config_id>')
@login_required
def delete_bank_config(config_id):
    """Admin-only: Delete bank config"""
    if session.get('role') != 'admin':
        flash('Chỉ Admin mới có quyền thực hiện thao tác này!', 'danger')
        return redirect(url_for('admin.manage_bank_configs'))

    from models.bank_config import BankConfig

    company_id = session.get('company_id')
    config = BankConfig.query.filter_by(id=config_id, company_id=company_id).first()

    if not config:
        flash("❌ Không tìm thấy cấu hình hoặc bạn không có quyền!", 'danger')
        return redirect(url_for('admin.manage_bank_configs'))

    try:
        bank_code = config.bank_code
        db.session.delete(config)
        db.session.commit()
        flash(f"✅ Đã xóa cấu hình {bank_code} thành công!", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"❌ Lỗi khi xóa: {str(e)}", 'danger')

    return redirect(url_for('admin.manage_bank_configs'))

# ============= Statement Config Routes =============

@main_bp.route('/user/statement-config/add', methods=['POST'])
@login_required
def add_statement_config():
    """Admin-only: Add statement config for company"""
    if session.get('role') != 'admin':
        flash('⚠️ Chỉ Admin mới có quyền thêm cấu hình sổ phụ!', 'danger')
        return redirect(url_for('admin.manage_statement_configs'))

    from models.bank_statement_config import BankStatementConfig

    company_id = session.get('company_id')
    if not company_id:
        flash("Vui lòng chọn công ty trước!", 'danger')
        return redirect(url_for('main.user_dashboard'))

    bank_code = request.form.get('bank_code', '').strip().upper()
    keywords = request.form.get('keywords', '').strip()
    col_keyword = request.form.get('col_keyword', '').strip()
    col_value = request.form.get('col_value', '').strip()
    row_start = request.form.get('row_start', '').strip()
    row_end = request.form.get('row_end', '').strip()
    identify_info = request.form.get('identify_info', '').strip()
    cell_format = request.form.get('cell_format', '').strip()

    if not bank_code or not keywords or not identify_info:
        flash("Mã ngân hàng, từ khóa và định danh không được để trống!", 'danger')
        return redirect(url_for('admin.manage_statement_configs'))

    # Convert keywords string to array
    keywords_array = [kw.strip() for kw in keywords.split(',') if kw.strip()]

    try:
        config = BankStatementConfig(
            company_id=company_id,
            bank_code=bank_code,
            keywords=keywords_array,
            col_keyword=col_keyword if col_keyword else None,
            col_value=col_value if col_value else None,
            row_start=int(row_start) if row_start else None,
            row_end=int(row_end) if row_end else None,
            identify_info=identify_info,
            cell_format=cell_format if cell_format else None
        )
        db.session.add(config)
        db.session.commit()
        flash(f"Đã thêm cấu hình sổ phụ {bank_code} thành công!", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Lỗi khi thêm cấu hình: {str(e)}", 'danger')

    return redirect(url_for('admin.manage_statement_configs'))

@main_bp.route('/user/statement-config/update/<int:config_id>', methods=['POST'])
@login_required
def update_statement_config(config_id):
    """Admin-only: Update statement config"""
    if session.get('role') != 'admin':
        flash('⚠️ Chỉ Admin mới có quyền sửa cấu hình sổ phụ!', 'danger')
        return redirect(url_for('admin.manage_statement_configs'))

    from models.bank_statement_config import BankStatementConfig

    company_id = session.get('company_id')
    config = BankStatementConfig.query.filter_by(id=config_id, company_id=company_id).first()

    if not config:
        flash("Không tìm thấy cấu hình hoặc bạn không có quyền!", 'danger')
        return redirect(url_for('admin.manage_statement_configs'))

    bank_code = request.form.get('bank_code', '').strip().upper()
    keywords = request.form.get('keywords', '').strip()
    col_keyword = request.form.get('col_keyword', '').strip()
    col_value = request.form.get('col_value', '').strip()
    row_start = request.form.get('row_start', '').strip()
    row_end = request.form.get('row_end', '').strip()
    identify_info = request.form.get('identify_info', '').strip()
    cell_format = request.form.get('cell_format', '').strip()

    if not bank_code or not keywords or not identify_info:
        flash("Mã ngân hàng, từ khóa và định danh không được để trống!", 'danger')
        return redirect(url_for('admin.manage_statement_configs'))

    # Convert keywords string to array
    keywords_array = [kw.strip() for kw in keywords.split(',') if kw.strip()]

    try:
        config.bank_code = bank_code
        config.keywords = keywords_array
        config.col_keyword = col_keyword if col_keyword else None
        config.col_value = col_value if col_value else None
        config.row_start = int(row_start) if row_start else None
        config.row_end = int(row_end) if row_end else None
        config.identify_info = identify_info
        config.cell_format = cell_format if cell_format else None
        db.session.commit()
        flash(f"Đã cập nhật cấu hình sổ phụ {bank_code} thành công!", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Lỗi khi cập nhật: {str(e)}", 'danger')

    return redirect(url_for('admin.manage_statement_configs'))

@main_bp.route('/user/statement-config/bulk-upload', methods=['POST'])
@login_required
def bulk_upload_statement_configs():
    """Admin only: Bulk upload statement configs from Excel/CSV file"""
    import logging
    # Chỉ cho phép admin upload
    if session.get('role') != 'admin':
        flash('⚠️ Chỉ Admin mới có quyền upload cấu hình sổ phụ theo lô!', 'danger')
        logging.warning(f"[UPLOAD BULK] User không phải admin: {session.get('username')}")
        return redirect(url_for('admin.manage_statement_configs'))

    from models.bank_statement_config import BankStatementConfig
    import pandas as pd
    import uuid
    import os
    from flask import current_app

    company_id = session.get('company_id')
    logging.info(f"[UPLOAD BULK] Start upload, user={session.get('username')}, company_id={company_id}")
    if not company_id:
        flash("Vui lòng chọn công ty trước!", 'danger')
        logging.warning(f"[UPLOAD BULK] Chưa chọn công ty")
        return redirect(url_for('admin.manage_statement_configs'))

    file = request.files.get('file')
    if not file or file.filename == '':
        flash("Vui lòng chọn file để upload!", 'danger')
        logging.warning(f"[UPLOAD BULK] Không có file upload")
        return redirect(url_for('admin.manage_statement_configs'))

    filename = secure_filename(file.filename)
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    logging.info(f"[UPLOAD BULK] File nhận: {filename}, ext={ext}")

    if ext not in ['xlsx', 'xls', 'csv']:
        flash("Chỉ hỗ trợ file Excel (.xlsx, .xls) hoặc CSV!", 'danger')
        logging.warning(f"[UPLOAD BULK] Định dạng file không hợp lệ: {ext}")
        return redirect(url_for('admin.manage_statement_configs'))

    temp_path = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), 'tmp', f"{uuid.uuid4().hex}.{ext}")
    os.makedirs(os.path.dirname(temp_path), exist_ok=True)
    file.save(temp_path)
    logging.info(f"[UPLOAD BULK] File lưu tạm: {temp_path}")

    try:
        if ext == 'csv':
            df = pd.read_csv(temp_path)
        else:
            df = pd.read_excel(temp_path)
        logging.info(f"[UPLOAD BULK] Đọc file thành công, shape={df.shape}")
        required_cols = ['bank_code', 'keywords', 'identify_info']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            flash(f"File thiếu các cột bắt buộc: {', '.join(missing_cols)}", 'danger')
            logging.error(f"[UPLOAD BULK] Thiếu cột: {missing_cols}")
            return redirect(url_for('admin.manage_statement_configs'))
        success_count = 0
        error_count = 0
        errors = []
        for idx, row in df.iterrows():
            try:
                bank_code = str(row.get('bank_code', '')).strip().upper()
                if not bank_code or bank_code == 'NAN':
                    errors.append(f"Dòng {idx + 2}: Thiếu bank_code")
                    error_count += 1
                    logging.warning(f"[UPLOAD BULK] Dòng {idx+2} thiếu bank_code")
                    continue
                keywords_str = str(row.get('keywords', '')).strip()
                if not keywords_str or keywords_str == 'nan':
                    errors.append(f"Dòng {idx + 2}: Thiếu keywords")
                    error_count += 1
                    logging.warning(f"[UPLOAD BULK] Dòng {idx+2} thiếu keywords")
                    continue
                keywords_array = [kw.strip() for kw in keywords_str.split(',') if kw.strip()]
                if not keywords_array:
                    errors.append(f"Dòng {idx + 2}: Keywords không hợp lệ")
                    error_count += 1
                    logging.warning(f"[UPLOAD BULK] Dòng {idx+2} keywords không hợp lệ")
                    continue
                identify_info = str(row.get('identify_info', '')).strip()
                identify_info = identify_info if identify_info != 'nan' else None
                col_keyword = str(row.get('col_keyword', '')).strip()
                col_keyword = col_keyword if col_keyword != 'nan' else None
                col_value = str(row.get('col_value', '')).strip()
                col_value = col_value if col_value != 'nan' else None
                row_start = row.get('row_start')
                row_start = int(row_start) if pd.notna(row_start) else None
                row_end = row.get('row_end')
                row_end = int(row_end) if pd.notna(row_end) else None
                cell_format = str(row.get('cell_format', '')).strip().lower()
                cell_format = cell_format if cell_format != 'nan' else None

                # Kiểm tra duplicate: nếu có identify_info thì dùng nó, không thì dùng keywords + col_keyword + col_value
                if identify_info:
                    existing = BankStatementConfig.query.filter_by(
                        company_id=company_id,
                        bank_code=bank_code,
                        identify_info=identify_info
                    ).first()
                else:
                    # Tìm theo keywords nếu không có identify_info
                    existing = None

                if existing:
                    existing.keywords = keywords_array
                    existing.col_keyword = col_keyword
                    existing.col_value = col_value
                    existing.row_start = row_start
                    existing.row_end = row_end
                    existing.cell_format = cell_format
                    success_count += 1
                    logging.info(f"[UPLOAD BULK] Update config dòng {idx+2} bank_code={bank_code} identify_info={identify_info}")
                else:
                    config = BankStatementConfig(
                        company_id=company_id,
                        bank_code=bank_code,
                        keywords=keywords_array,
                        col_keyword=col_keyword,
                        col_value=col_value,
                        row_start=row_start,
                        row_end=row_end,
                        identify_info=identify_info,
                        cell_format=cell_format
                    )
                    db.session.add(config)
                    success_count += 1
                    logging.info(f"[UPLOAD BULK] Thêm mới dòng {idx+2} bank_code={bank_code} identify_info={identify_info}")
            except Exception as e:
                errors.append(f"Dòng {idx + 2}: {str(e)}")
                error_count += 1
                logging.error(f"[UPLOAD BULK] Lỗi dòng {idx+2}: {e}")
        db.session.commit()
        logging.info(f"[UPLOAD BULK] Commit xong, success={success_count}, error={error_count}")
        if success_count > 0:
            flash(f"✅ Đã upload thành công {success_count} cấu hình!", 'success')
        if error_count > 0:
            flash(f"⚠️ {error_count} dòng bị lỗi", 'warning')
            for err in errors[:5]:
                flash(err, 'warning')
            if len(errors) > 5:
                flash(f"... và {len(errors) - 5} lỗi khác", 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f"Lỗi khi đọc file: {str(e)}", 'danger')
        logging.error(f"[UPLOAD BULK] Lỗi tổng: {e}")
    finally:
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
                logging.info(f"[UPLOAD BULK] Đã xóa file tạm: {temp_path}")
        except Exception as e:
            logging.error(f"[UPLOAD BULK] Lỗi xóa file tạm: {e}")
    bank_code_filter = request.form.get('bank_code', '')
    if bank_code_filter:
        return redirect(url_for('admin.manage_statement_configs', bank_code=bank_code_filter))
    return redirect(url_for('admin.manage_statement_configs'))

@main_bp.route('/user/statement-config/template')
@login_required
def download_statement_config_template():
    """User/Admin: Generate and download a template Excel file for bulk upload"""
    # Cho phép cả user và admin tải template
    if session.get('role') not in ['user', 'admin']:
        flash('Bạn không có quyền thực hiện thao tác này!', 'danger')
        return redirect(url_for('main.user_dashboard'))

    import pandas as pd
    from io import BytesIO

    # Create sample data with multiple configs for same bank_code
    template_data = {
        'bank_code': ['VCB', 'VCB', 'VCB', 'VCB', 'VCB', 'VCB', 'VCB', 'VCB', 'VCB', 'VCB', 'VCB', 'VCB'],
        'keywords': [
            'Số tài khoản,Account Number,Account No',
            'Loại tiền,Currency',
            'Số dư đầu kỳ,Opening Balance',
            'Số dư cuối kỳ,Closing Balance',
            'Diễn giải,Narrative,Description',
            'Ngày GD,Transaction Date,Date',
            'Số tiền ghi nợ,Debit,Dr',
            'Số tiền ghi có,Credit,Cr',
            'Mã luồng,Flow Code',
            'Phí giao dịch,Transaction Fee,Fee',
            'VAT,Transaction VAT',
            'Thông tin định danh,Identify Info'
        ],
        'col_keyword': ['A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A'],
        'col_value': ['B', 'B', 'B', 'B', 'B', 'B', 'B', 'B', 'B', 'B', 'B', 'B'],
        'row_start': [1, 2, 3, 4, 10, 10, 10, 10, 10, 10, 10, 10],
        'row_end': [1, 2, 3, 4, 100, 100, 100, 100, 100, 100, 100, 100],
        'identify_info': [
            'accountno',
            'currency',
            'openingbalance',
            'closingbalance',
            'narrative',
            'transactiondate',
            'debit',
            'credit',
            'flowcode',
            'transactionfee',
            'transactionvat',
            'identify_info'
        ],
        'cell_format': ['Text', 'Text', 'Number', 'Number', 'Text', 'Date', 'Number', 'Number', 'Text', 'Number', 'Number', 'Text']
    }

    df = pd.DataFrame(template_data)

    # Create Excel file in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Template')

        # Auto-adjust column widths
        worksheet = writer.sheets['Template']
        for idx, col in enumerate(df.columns):
            max_length = max(df[col].astype(str).apply(len).max(), len(col)) + 2
            worksheet.column_dimensions[chr(65 + idx)].width = min(max_length, 50)  # Cap at 50

    output.seek(0)

    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='statement_config_template.xlsx'
    )

@main_bp.route('/user/statement-config/delete/<int:config_id>')
@login_required
def delete_statement_config(config_id):
    """Admin-only: Delete statement config"""
    if session.get('role') != 'admin':
        flash('⚠️ Chỉ Admin mới có quyền thực hiện thao tác này!', 'danger')
        return redirect(url_for('admin.manage_statement_configs'))

    from models.bank_statement_config import BankStatementConfig

    company_id = session.get('company_id')
    config = BankStatementConfig.query.filter_by(id=config_id, company_id=company_id).first()

    if not config:
        flash("Không tìm thấy cấu hình hoặc bạn không có quyền!", 'danger')
        return redirect(url_for('admin.manage_statement_configs'))

    try:
        db.session.delete(config)
        db.session.commit()
        flash(f"Đã xóa cấu hình {config.bank_code} thành công!", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Lỗi khi xóa: {str(e)}", 'danger')

    return redirect(url_for('admin.manage_statement_configs'))

@main_bp.route('/user/statement-config/delete-by-bank', methods=['POST'])
@login_required
def delete_statement_configs_by_bank():
    """Admin-only: Bulk delete all statement configs for a given bank_code in the current company."""
    if session.get('role') != 'admin':
        flash('⚠️ Chỉ Admin mới có quyền xóa cấu hình theo bank_code!', 'danger')
        return redirect(url_for('admin.manage_statement_configs'))

    from models.bank_statement_config import BankStatementConfig

    company_id = session.get('company_id')
    if not company_id:
        flash('Vui lòng chọn công ty trước!', 'warning')
        return redirect(url_for('admin.manage_statement_configs'))

    bank_code = (request.form.get('bank_code') or '').strip().upper()
    if not bank_code:
        flash('Vui lòng nhập mã ngân hàng hợp lệ.', 'warning')
        return redirect(url_for('admin.manage_statement_configs'))

    try:
        q = BankStatementConfig.query.filter_by(company_id=company_id, bank_code=bank_code)
        count = q.count()
        if count == 0:
            flash(f'Không tìm thấy cấu hình nào cho {bank_code}.', 'info')
            return redirect(url_for('admin.manage_statement_configs'))

        q.delete(synchronize_session=False)
        db.session.commit()
        flash(f'Đã xóa {count} cấu hình sổ phụ cho ngân hàng {bank_code}.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Xóa thất bại: {e}', 'danger')

    # Redirect về admin statement configs
    return redirect(url_for('admin.manage_statement_configs'))

@main_bp.route('/statement/upload-to-sftp/<int:log_id>', methods=['POST'])
@login_required
def upload_statement_to_sftp(log_id):
    '''Upload MT940 file to SFTP server'''
    from models.company import Company
    from services.sftp_service import SFTPService
    from datetime import datetime
    from flask import jsonify

    try:
        log = StatementLog.query.get(log_id)
        if not log:
            return jsonify({'success': False, 'status': 'error', 'message': 'Không tìm thấy log'}), 404

        # Permission: allow admin OR owner user OR same-company user
        allowed = False
        if session.get('role') == 'admin':
            allowed = True
        elif log.user_id and log.user_id == session.get('user_id'):
            allowed = True
        elif log.company_id and log.company_id == session.get('company_id'):
            allowed = True

        if not allowed:
            return jsonify({'success': False, 'status': 'error', 'message': 'Bạn không có quyền upload log này'}), 403

        if not log.mt940_filename:
            return jsonify({'success': False, 'status': 'error', 'message': 'File MT940 chưa được tạo'}), 400

        company = Company.query.get(log.company_id)
        if not company:
            return jsonify({'success': False, 'status': 'error', 'message': 'Không tìm thấy thông tin công ty'}), 404

        if not company.sftp_host:
            return jsonify({
                'success': False,
                'status': 'error',
                'message': 'Công ty chưa cấu hình SFTP. Vui lòng liên hệ admin để cấu hình: SFTP Host, Port, Username, Password và Remote Path'
            }), 400

        # Validate all required SFTP fields
        missing_fields = []
        if not company.sftp_host:
            missing_fields.append('SFTP Host')
        if not company.sftp_port:
            missing_fields.append('SFTP Port')
        if not company.sftp_username:
            missing_fields.append('SFTP Username')
        if not company.sftp_password and not company.sftp_private_key_path:
            missing_fields.append('SFTP Password hoặc Private Key')
        if not company.sftp_remote_path:
            missing_fields.append('SFTP Remote Path')

        if missing_fields:
            return jsonify({
                'success': False,
                'status': 'error',
                'message': f'Thiếu thông tin SFTP: {", ".join(missing_fields)}. Vui lòng liên hệ admin để cấu hình.'
            }), 400

        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        mt940_path = os.path.join(upload_folder, log.mt940_filename)

        if not os.path.exists(mt940_path):
            return jsonify({'success': False, 'status': 'error', 'message': f'File MT940 không tồn tại'}), 404

        current_app.logger.info(f'Uploading MT940 file: {mt940_path} for log_id={log_id}')

        result = SFTPService.upload_file(
            local_file_path=mt940_path,
            company=company,
            original_filename=log.mt940_filename
        )

        log.sftp_uploaded = result['success']
        log.sftp_uploaded_at = datetime.now() if result['success'] else None
        log.sftp_remote_path = result.get('remote_path')
        log.sftp_upload_message = result['message']

        db.session.commit()

        return jsonify({
            'success': result['success'],
            'status': 'success' if result['success'] else 'error',
            'message': result['message'],
            'remote_path': result.get('remote_path'),
            'uploaded_at': log.sftp_uploaded_at.strftime('%Y-%m-%d %H:%M:%S') if log.sftp_uploaded_at else None
        }), 200 if result['success'] else 500

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error uploading to SFTP: {e}', exc_info=True)
        return jsonify({'success': False, 'status': 'error', 'message': f'Lỗi: {str(e)}'}), 500


@main_bp.route('/statement/upload-to-sftp-bulk', methods=['POST'])
@login_required
def upload_statement_to_sftp_bulk():
    """Bulk upload multiple MT940 files to SFTP server.
    Input JSON: {"ids": [1,2,3]}
    Response JSON summarizes per-id results.
    Permission per item: admin OR owner user OR same-company user.
    """
    from models.company import Company
    from services.sftp_service import SFTPService
    from flask import jsonify
    data = request.get_json(silent=True) or {}
    ids = data.get('ids') or []
    if not isinstance(ids, list) or not ids:
        return jsonify({'success': False, 'status': 'error', 'message': 'Thiếu danh sách IDs', 'results': []}), 400

    results = []
    success_count = 0
    failure_count = 0

    for _id in ids:
        try:
            try:
                log_id = int(_id)
            except Exception:
                results.append({'id': _id, 'success': False, 'message': 'ID không hợp lệ'})
                failure_count += 1
                continue

            stmt = StatementLog.query.get(log_id)
            if not stmt:
                results.append({'id': log_id, 'success': False, 'message': 'Không tìm thấy log'})
                failure_count += 1
                continue

            # permission per item
            allowed = False
            if session.get('role') == 'admin':
                allowed = True
            elif stmt.user_id and stmt.user_id == session.get('user_id'):
                allowed = True
            elif stmt.company_id and stmt.company_id == session.get('company_id'):
                allowed = True
            if not allowed:
                results.append({'id': log_id, 'success': False, 'message': 'Không có quyền'})
                failure_count += 1
                continue

            if not stmt.mt940_filename:
                results.append({'id': log_id, 'success': False, 'message': 'File MT940 chưa được tạo'})
                failure_count += 1
                continue

            company = Company.query.get(stmt.company_id)
            if not company:
                results.append({'id': log_id, 'success': False, 'message': 'Không tìm thấy thông tin công ty'})
                failure_count += 1
                continue

            # Validate minimal SFTP fields; detailed validation happens inside upload service and route
            if not company.sftp_host or not company.sftp_username or (not company.sftp_password and not company.sftp_private_key_path) or not company.sftp_remote_path:
                results.append({'id': log_id, 'success': False, 'message': 'Thiếu cấu hình SFTP của công ty'})
                failure_count += 1
                continue

            upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
            mt940_path = os.path.join(upload_folder, stmt.mt940_filename)
            if not os.path.exists(mt940_path):
                results.append({'id': log_id, 'success': False, 'message': 'File MT940 không tồn tại'})
                failure_count += 1
                continue

            # perform upload
            res = SFTPService.upload_file(
                local_file_path=mt940_path,
                company=company,
                original_filename=stmt.mt940_filename
            )

            # update stmt status
            stmt.sftp_uploaded = res.get('success', False)
            stmt.sftp_uploaded_at = datetime.now() if stmt.sftp_uploaded else None
            stmt.sftp_remote_path = res.get('remote_path')
            stmt.sftp_upload_message = res.get('message')
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
                # still report failure for this item
                results.append({'id': log_id, 'success': False, 'message': 'Lỗi cập nhật database sau khi upload'})
                failure_count += 1
                continue

            if stmt.sftp_uploaded:
                success_count += 1
            else:
                failure_count += 1
            results.append({'id': log_id, 'success': stmt.sftp_uploaded, 'message': res.get('message'), 'remote_path': stmt.sftp_remote_path})

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Bulk SFTP error for id={_id}: {e}', exc_info=True)
            results.append({'id': _id, 'success': False, 'message': f'Lỗi: {str(e)}'})
            failure_count += 1

    overall_success = success_count > 0 and failure_count == 0
    return jsonify({
        'success': overall_success,
        'status': 'success' if overall_success else 'partial' if success_count > 0 else 'error',
        'success_count': success_count,
        'failure_count': failure_count,
        'results': results
    }), 200
