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


@main_bp.route('/bank-configs')
@user_required
def user_bank_configs():
    from models.bank_config import BankConfig
    company_id = session.get('company_id')
    bank_configs = []
    if company_id:
        bank_configs = BankConfig.query.filter_by(company_id=company_id).order_by(BankConfig.bank_code.asc()).all()
    return render_template('bank_configs_page.html', username=session.get('username'), companies=None, current_company_id=company_id, bank_configs=bank_configs)


@main_bp.route('/statement-configs')
@user_required
def user_statement_configs():
    from models.bank_statement_config import BankStatementConfig
    company_id = session.get('company_id')
    statement_configs = []
    if company_id:
        statement_configs = BankStatementConfig.query.filter_by(company_id=company_id).order_by(BankStatementConfig.bank_code.asc()).all()
    return render_template('statement_configs_page.html', username=session.get('username'), companies=None, current_company_id=company_id, statement_configs=statement_configs)

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
                        if parse_result.get('status') == 'SUCCESS':
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
                    if parse_result.get('status') == 'SUCCESS':
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
    
    bank_code = request.args.get('bank_code')
    status = request.args.get('status')
    days = request.args.get('days', type=int, default=7)
    
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
        
    logs = query.order_by(BankLog.processed_at.desc()).all()
    
    return render_template('user_logs.html', 
                         logs=logs,
                         username=session.get('username'),
                         company_name=session.get('company_name'),
                         companies=companies,
                         current_company_id=company_id)


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

    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': total_pages,
        'has_prev': page > 1,
        'has_next': page < total_pages,
    }

    return render_template('statement_logs.html', logs=logs, banks=banks, username=session.get('username'), pagination=pagination)


@main_bp.route('/user/statement-log/<int:log_id>/download')
@user_required
def download_statement_mt940(log_id):
    stmt = StatementLog.query.filter_by(id=log_id, user_id=session['user_id']).first()
    if not stmt:
        abort(404)
    if not stmt.mt940_filename:
        abort(404)
    full_path = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), stmt.mt940_filename)
    if not os.path.exists(full_path):
        abort(404)
    return send_file(full_path, as_attachment=True)


@main_bp.route('/user/statement-log/<int:log_id>')
@user_required
def view_statement_detail(log_id):
    """Show parsed statement header and details."""
    stmt = StatementLog.query.filter_by(id=log_id, user_id=session['user_id']).first()
    if not stmt:
        # also allow company owners to view statements for their company users
        stmt = StatementLog.query.filter_by(id=log_id, company_id=session.get('company_id')).first()
    if not stmt:
        abort(404)

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
@user_required
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

    # redirect back to dashboard
    return redirect(url_for('main.user_dashboard'))

@main_bp.route('/user/bank-config/add', methods=['POST'])
@user_required
def add_bank_config():
    """Add bank config for user's company"""
    from models.bank_config import BankConfig
    
    company_id = session.get('company_id')
    if not company_id:
        flash("Vui lòng chọn công ty trước!", 'danger')
        return redirect(url_for('main.user_bank_configs'))
    
    bank_code = request.form.get('bank_code', '').strip().upper()
    bank_name = request.form.get('bank_name', '').strip()
    keywords = request.form.get('keywords', '').strip()
    
    if not bank_code or not keywords:
        flash("Mã ngân hàng và từ khóa không được để trống!", 'danger')
        return redirect(url_for('main.user_bank_configs'))
    
    # Convert keywords string to array
    keywords_array = [kw.strip() for kw in keywords.split(',') if kw.strip()]
    
    try:
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
        flash(f"Đã thêm cấu hình ngân hàng {bank_code} thành công!", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Lỗi khi thêm cấu hình: {str(e)}", 'danger')
    
    return redirect(url_for('main.user_bank_configs'))

@main_bp.route('/user/bank-config/update/<int:config_id>', methods=['POST'])
@user_required
def update_bank_config(config_id):
    """Update bank config"""
    from models.bank_config import BankConfig
    
    company_id = session.get('company_id')
    config = BankConfig.query.filter_by(id=config_id, company_id=company_id).first()
    
    if not config:
        flash("Không tìm thấy cấu hình hoặc bạn không có quyền!", 'danger')
        return redirect(url_for('main.user_bank_configs'))
    
    bank_code = request.form.get('bank_code', '').strip().upper()
    bank_name = request.form.get('bank_name', '').strip()
    keywords = request.form.get('keywords', '').strip()
    
    if not bank_code or not keywords:
        flash("Mã ngân hàng và từ khóa không được để trống!", 'danger')
        return redirect(url_for('main.user_dashboard'))
    
    # Convert keywords string to array
    keywords_array = [kw.strip() for kw in keywords.split(',') if kw.strip()]
    
    try:
        config.bank_code = bank_code
        config.bank_name = bank_name if bank_name else None
        config.keywords = keywords_array
        db.session.commit()
        flash(f"Đã cập nhật cấu hình {bank_code} thành công!", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Lỗi khi cập nhật: {str(e)}", 'danger')
    
    return redirect(url_for('main.user_bank_configs'))

@main_bp.route('/user/bank-config/delete/<int:config_id>')
@user_required
def delete_bank_config(config_id):
    """Delete bank config"""
    from models.bank_config import BankConfig
    
    company_id = session.get('company_id')
    config = BankConfig.query.filter_by(id=config_id, company_id=company_id).first()
    
    if not config:
        flash("Không tìm thấy cấu hình hoặc bạn không có quyền!", 'danger')
        return redirect(url_for('main.user_bank_configs'))
    
    try:
        db.session.delete(config)
        db.session.commit()
        flash(f"Đã xóa cấu hình {config.bank_code} thành công!", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Lỗi khi xóa: {str(e)}", 'danger')
    
    return redirect(url_for('main.user_bank_configs'))

# ============= Statement Config Routes =============

@main_bp.route('/user/statement-config/add', methods=['POST'])
@user_required
def add_statement_config():
    """Add statement config for user's company"""
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
        return redirect(url_for('main.user_statement_configs'))
    
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
    
    return redirect(url_for('main.user_statement_configs'))

@main_bp.route('/user/statement-config/update/<int:config_id>', methods=['POST'])
@user_required
def update_statement_config(config_id):
    """Update statement config"""
    from models.bank_statement_config import BankStatementConfig
    
    company_id = session.get('company_id')
    config = BankStatementConfig.query.filter_by(id=config_id, company_id=company_id).first()
    
    if not config:
        flash("Không tìm thấy cấu hình hoặc bạn không có quyền!", 'danger')
        return redirect(url_for('main.user_statement_configs'))
    
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
        return redirect(url_for('main.user_dashboard'))
    
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
    
    return redirect(url_for('main.user_statement_configs'))

@main_bp.route('/user/statement-config/delete/<int:config_id>')
@user_required
def delete_statement_config(config_id):
    """Delete statement config"""
    from models.bank_statement_config import BankStatementConfig
    
    company_id = session.get('company_id')
    config = BankStatementConfig.query.filter_by(id=config_id, company_id=company_id).first()
    
    if not config:
        flash("Không tìm thấy cấu hình hoặc bạn không có quyền!", 'danger')
        return redirect(url_for('main.user_statement_configs'))
    
    try:
        db.session.delete(config)
        db.session.commit()
        flash(f"Đã xóa cấu hình {config.bank_code} thành công!", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Lỗi khi xóa: {str(e)}", 'danger')
    
    return redirect(url_for('main.user_statement_configs'))