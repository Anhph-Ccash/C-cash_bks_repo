from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from extensions import db
from models import User
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import SQLAlchemyError
import os
import uuid
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin')
def admin():
    """Redirect to users page by default"""
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/admin/admin-users')
def manage_users():
    """Manage Users Page"""
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))

    from models.company import Company
    import math

    # Pagination parameters for users
    page = request.args.get('page', type=int, default=1)
    per_page = request.args.get('per_page', type=int, default=10)
    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 10

    # Get users with pagination
    user_query = User.query
    total_users = user_query.count()
    total_pages = max(1, math.ceil(total_users / per_page))
    if page > total_pages:
        page = total_pages

    offset = (page - 1) * per_page
    users = user_query.order_by(User.id.asc()).offset(offset).limit(per_page).all()

    # Pagination info
    user_pagination = {
        'page': page,
        'per_page': per_page,
        'total': total_users,
        'total_pages': total_pages,
        'has_prev': page > 1,
        'has_next': page < total_pages,
    }

    # Get all companies for dropdown
    companies = Company.query.filter_by(is_active=True).all()

    # Get current company from session
    current_company_id = session.get('company_id')
    company_name = session.get('company_name')

    return render_template('admin_users.html',
                         users=users,
                         user_pagination=user_pagination,
                         username=session.get('username'),
                         companies=companies,
                         current_company_id=current_company_id,
                         company_name=company_name)

@admin_bp.route('/admin/admin-companies')
def manage_companies():
    """Manage Companies Page"""
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))

    from models.company import Company

    # Get all companies
    companies = Company.query.filter_by(is_active=True).all()

    # Get current company from session
    current_company_id = session.get('company_id')
    company_name = session.get('company_name')

    return render_template('admin_companies.html',
                         username=session.get('username'),
                         companies=companies,
                         current_company_id=current_company_id,
                         company_name=company_name)

@admin_bp.route('/admin/admin-bank-configs')
def manage_bank_configs():
    """Manage Bank Configs Page - Allow both user and admin"""
    # Cho phép cả user và admin truy cập
    if not session.get('user_id'):
        return redirect(url_for('auth.login'))

    from models.company import Company
    from models.bank_config import BankConfig
    import math

    # Get current company from session
    company_id = session.get('company_id')
    if not company_id:
        flash('⚠️ Vui lòng chọn công ty trước!', 'warning')
        companies = Company.query.filter_by(is_active=True).all()
        return render_template('admin_bank_configs.html',
                             username=session.get('username'),
                             companies=companies,
                             current_company_id=None,
                             company_name=None,
                             bank_configs=[],
                             bank_code_filter='',
                             bank_pagination={'page': 1, 'per_page': 10, 'total': 0, 'total_pages': 1, 'has_prev': False, 'has_next': False})

    # Filter parameter
    bank_code_filter = request.args.get('bank_code', '').strip()

    # Pagination for bank configs
    bank_page = request.args.get('page', type=int, default=1)
    bank_per_page = request.args.get('per_page', type=int, default=10)
    if bank_page < 1:
        bank_page = 1
    if bank_per_page < 1:
        bank_per_page = 10

    # Apply company filter and optional bank_code filter
    bank_query = BankConfig.query.filter_by(company_id=company_id)
    if bank_code_filter:
        bank_query = bank_query.filter(BankConfig.bank_code.ilike(f'%{bank_code_filter}%'))
    bank_query = bank_query.order_by(BankConfig.bank_code.asc())
    total_banks = bank_query.count()
    total_bank_pages = max(1, math.ceil(total_banks / bank_per_page))
    if bank_page > total_bank_pages:
        bank_page = total_bank_pages

    bank_offset = (bank_page - 1) * bank_per_page
    bank_configs = bank_query.offset(bank_offset).limit(bank_per_page).all()

    bank_pagination = {
        'page': bank_page,
        'per_page': bank_per_page,
        'total': total_banks,
        'total_pages': total_bank_pages,
        'has_prev': bank_page > 1,
        'has_next': bank_page < total_bank_pages,
    }

    # Get all companies for dropdown
    companies = Company.query.filter_by(is_active=True).all()
    company_name = session.get('company_name')

    return render_template('admin_bank_configs.html',
                         username=session.get('username'),
                         companies=companies,
                         current_company_id=company_id,
                         company_name=company_name,
                         bank_configs=bank_configs,
                         bank_code_filter=bank_code_filter,
                         bank_pagination=bank_pagination)

@admin_bp.route('/admin/admin-statement-configs')
def manage_statement_configs():
    """Manage Statement Configs Page - Admin only"""
    # Chỉ cho phép admin truy cập
    if session.get('role') != 'admin':
        flash('⚠️ Chỉ Admin mới có quyền quản lý cấu hình sổ phụ!', 'danger')
        return redirect(url_for('main.user_dashboard'))

    from models.company import Company
    from models.bank_statement_config import BankStatementConfig
    import math

    # Get current company from session
    company_id = session.get('company_id')
    if not company_id:
        flash('⚠️ Vui lòng chọn công ty trước!', 'warning')
        companies = Company.query.filter_by(is_active=True).all()
        return render_template('admin_statement_configs.html',
                             username=session.get('username'),
                             companies=companies,
                             current_company_id=None,
                             company_name=None,
                             statement_configs=[],
                             stmt_pagination={'page': 1, 'per_page': 12, 'total': 0, 'total_pages': 1, 'has_prev': False, 'has_next': False})

    # Get filter parameter
    bank_code_filter = request.args.get('bank_code', '').strip().upper()

    # Pagination for statement configs
    page = request.args.get('page', type=int, default=1)
    per_page = request.args.get('per_page', type=int, default=12)
    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 12

    # Build query with company filter and optional bank_code filter
    stmt_query = BankStatementConfig.query.filter_by(company_id=company_id)

    if bank_code_filter:
        stmt_query = stmt_query.filter(BankStatementConfig.bank_code.ilike(f'%{bank_code_filter}%'))

    # Sort by ID instead of bank_code
    stmt_query = stmt_query.order_by(BankStatementConfig.id.asc())

    total_stmts = stmt_query.count()
    total_pages = max(1, math.ceil(total_stmts / per_page))
    if page > total_pages:
        page = total_pages

    offset = (page - 1) * per_page
    statement_configs = stmt_query.offset(offset).limit(per_page).all()

    stmt_pagination = {
        'page': page,
        'per_page': per_page,
        'total': total_stmts,
        'total_pages': total_pages,
        'has_prev': page > 1,
        'has_next': page < total_pages,
    }

    # Get all companies for dropdown
    companies = Company.query.filter_by(is_active=True).all()
    company_name = session.get('company_name')

    return render_template('admin_statement_configs.html',
                         username=session.get('username'),
                         companies=companies,
                         current_company_id=company_id,
                         company_name=company_name,
                         statement_configs=statement_configs,
                         stmt_pagination=stmt_pagination,
                         bank_code_filter=bank_code_filter)

@admin_bp.route('/admin/user/add', methods=['POST'])
def add_user():
    if session.get('role') != 'admin':
        flash('Bạn không có quyền thêm user', 'danger')
        return redirect(url_for('admin.manage_users'))

    from models.user_company import UserCompany

    try:
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        role = request.form.get('role', 'user')
        company_ids = request.form.getlist('company_ids[]')

        # Validation
        if not username or not email or not password:
            flash('Vui lòng điền đầy đủ thông tin bắt buộc!', 'danger')
            return redirect(url_for('admin.manage_users'))

        if not company_ids:
            flash('Vui lòng chọn ít nhất một công ty!', 'danger')
            return redirect(url_for('admin.manage_users'))

        # Check if username already exists
        if User.query.filter_by(username=username).first():
            flash(f'Username "{username}" đã tồn tại!', 'danger')
            return redirect(url_for('admin.manage_users'))

        # Check if email already exists
        if User.query.filter_by(email=email).first():
            flash(f'Email "{email}" đã tồn tại!', 'danger')
            return redirect(url_for('admin.manage_users'))

        user = User(username=username,
                   email=email,
                   role=role,
                   password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.flush()  # Get user.id before commit

        # Add user-company relationships
        for company_id in company_ids:
            if company_id:
                user_company = UserCompany(user_id=user.id, company_id=int(company_id))
                db.session.add(user_company)

        db.session.commit()
        flash(f'✅ Đã thêm user: {username}', 'success')
    except SQLAlchemyError as e:
        db.session.rollback()
        flash(f'❌ Lỗi khi thêm user: {str(e)}', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'❌ Lỗi: {str(e)}', 'danger')

    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/admin/update-user/<int:user_id>', methods=['GET', 'POST'])
def update_user(user_id):
    from flask import current_app

    current_app.logger.info(f"=== UPDATE USER {user_id} START ===")
    current_app.logger.info(f"Request method: {request.method}")
    current_app.logger.info(f"Session role: {session.get('role')}")

    if session.get('role') != 'admin':
        flash('Bạn không có quyền cập nhật user', 'danger')
        return redirect(url_for('admin.manage_users'))

    from models import User, UserCompany
    from werkzeug.security import generate_password_hash

    user = User.query.get(user_id)
    if not user:
        current_app.logger.error(f"User {user_id} not found")
        flash('Không tìm thấy user', 'danger')
        return redirect(url_for('admin.manage_users'))

    # If GET request, redirect to users page
    if request.method == 'GET':
        current_app.logger.info("GET request, redirecting to manage_users")
        return redirect(url_for('admin.manage_users'))

    current_app.logger.info(f"Request form data: {dict(request.form)}")

    try:
        # Update basic info
        new_username = request.form['username']
        new_email = request.form['email']
        new_role = request.form['role']

        current_app.logger.info(f"Old values - username: {user.username}, email: {user.email}, role: {user.role}")
        current_app.logger.info(f"New values - username: {new_username}, email: {new_email}, role: {new_role}")

        user.username = new_username
        user.email = new_email
        user.role = new_role

        # Update password only if provided
        password = request.form.get('password', '').strip()
        if password:
            current_app.logger.info("Password provided, updating password hash")
            user.password_hash = generate_password_hash(password)
        else:
            current_app.logger.info("No password provided, keeping existing password")

        # Update companies
        company_ids = request.form.getlist('company_ids[]')
        current_app.logger.info(f"Company IDs from form: {company_ids}")

        if company_ids:
            # Remove old associations
            old_count = UserCompany.query.filter_by(user_id=user.id).count()
            current_app.logger.info(f"Removing {old_count} old company associations")
            UserCompany.query.filter_by(user_id=user.id).delete()

            # Add new associations
            for cid in company_ids:
                current_app.logger.info(f"Adding company association: user_id={user.id}, company_id={cid}")
                user_company = UserCompany(user_id=user.id, company_id=int(cid))
                db.session.add(user_company)
        else:
            current_app.logger.warning("No company IDs provided!")

        current_app.logger.info("Committing changes to database...")
        db.session.commit()
        current_app.logger.info("✅ Update successful!")
        flash(f'Đã cập nhật user: {user.username}', 'success')

    except KeyError as e:
        db.session.rollback()
        error_msg = f'Thiếu trường bắt buộc: {str(e)}'
        current_app.logger.error(error_msg, exc_info=True)
        flash(error_msg, 'danger')
    except Exception as e:
        db.session.rollback()
        error_msg = f'Lỗi khi cập nhật user: {str(e)}'
        current_app.logger.error(error_msg, exc_info=True)
        flash(error_msg, 'danger')

    current_app.logger.info("=== UPDATE USER END ===")
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/admin/user/delete/<int:user_id>')
def delete_user(user_id):
    if session.get('role') != 'admin':
        flash('Bạn không có quyền xóa user', 'danger')
        return redirect(url_for('admin.manage_users'))

    user = User.query.get(user_id)
    if not user:
        flash('Không tìm thấy user', 'danger')
        return redirect(url_for('admin.manage_users'))

    try:
        username = user.username
        db.session.delete(user)
        db.session.commit()
        flash(f'Đã xóa user: {username}', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Lỗi khi xóa user: {str(e)}', 'danger')

    return redirect(url_for('admin.manage_users'))

# Company Management Routes
@admin_bp.route('/admin/company/add', methods=['POST'])
def add_company():
    if session.get('role') != 'admin':
        flash('Bạn không có quyền thêm company', 'danger')
        return redirect(url_for('admin.manage_companies'))

    from models.company import Company

    try:
        name = request.form['name']
        address = request.form.get('address', '')
        tax_code = request.form.get('tax_code', '')

        # SFTP information
        sftp_host = request.form.get('sftp_host', '').strip() or None
        sftp_port = request.form.get('sftp_port', type=int) or 22
        sftp_username = request.form.get('sftp_username', '').strip() or None
        sftp_password = request.form.get('sftp_password', '').strip() or None
        sftp_remote_path = request.form.get('sftp_remote_path', '').strip() or None
        sftp_private_key_path = request.form.get('sftp_private_key_path', '').strip() or None

        company = Company(
            name=name,
            address=address,
            tax_code=tax_code,
            is_active=True,
            sftp_host=sftp_host,
            sftp_port=sftp_port,
            sftp_username=sftp_username,
            sftp_password=sftp_password,
            sftp_remote_path=sftp_remote_path,
            sftp_private_key_path=sftp_private_key_path
        )
        db.session.add(company)
        db.session.commit()
        flash(f'Đã thêm công ty: {name}', 'success')
        return redirect(url_for('admin.manage_companies'))
    except SQLAlchemyError as e:
        db.session.rollback()
        flash(f'Lỗi khi thêm công ty: {str(e)}', 'danger')
        return redirect(url_for('admin.manage_companies'))

@admin_bp.route('/admin/company/update/<int:company_id>', methods=['POST'])
def update_company(company_id):
    if session.get('role') != 'admin':
        flash('Bạn không có quyền cập nhật', 'danger')
        return redirect(url_for('admin.manage_companies'))

    from models.company import Company

    company = Company.query.get(company_id)
    if not company:
        flash('Không tìm thấy company', 'danger')
        return redirect(url_for('admin.manage_companies'))

    try:
        company.name = request.form['name']
        company.address = request.form.get('address', '')
        company.tax_code = request.form.get('tax_code', '')

        # Update SFTP information
        company.sftp_host = request.form.get('sftp_host', '').strip() or None
        company.sftp_port = request.form.get('sftp_port', type=int) or 22
        company.sftp_username = request.form.get('sftp_username', '').strip() or None

        # Only update password if provided
        sftp_password = request.form.get('sftp_password', '').strip()
        if sftp_password:
            company.sftp_password = sftp_password

        company.sftp_remote_path = request.form.get('sftp_remote_path', '').strip() or None
        company.sftp_private_key_path = request.form.get('sftp_private_key_path', '').strip() or None

        db.session.commit()
        flash(f'Đã cập nhật công ty: {company.name}', 'success')
        return redirect(url_for('admin.manage_companies'))
    except SQLAlchemyError as e:
        db.session.rollback()
        flash(f'Lỗi khi cập nhật: {str(e)}', 'danger')
        return redirect(url_for('admin.manage_companies'))

@admin_bp.route('/admin/company/delete/<int:company_id>')
def delete_company(company_id):
    if session.get('role') != 'admin':
        return "Bạn không có quyền xóa", 403

    from models.company import Company

    company = Company.query.get(company_id)
    if not company:
        return "Không tìm thấy company", 404

    try:
        db.session.delete(company)
        db.session.commit()
        return redirect(url_for('admin.manage_companies'))
    except SQLAlchemyError as e:
        db.session.rollback()
        return str(e), 500


# ============================================================
# UPLOAD & LOGS ROUTES (moved from upload blueprint)
# ============================================================

@admin_bp.route('/admin/admin-upload', methods=['GET'])
def admin_upload_page():
    """Admin upload page - show upload form with paginated statement logs on the same page."""
    if session.get('role') != 'admin':
        flash('Chỉ admin mới có quyền truy cập!', 'danger')
        return redirect(url_for('auth.login'))

    from models.company import Company
    from models.statement_log import StatementLog
    from models.bank_log import BankLog
    import math

    # Get all companies for admin
    companies = Company.query.filter_by(is_active=True).all()
    current_company_id = session.get('company_id')
    company_name = session.get('company_name')

    # Pagination params for statement logs
    page = request.args.get('page', type=int, default=1)
    per_page = request.args.get('per_page', type=int, default=50)  # Increased from 15 to 50
    if page and page < 1:
        page = 1
    if per_page and per_page < 1:
        per_page = 50

    # Filter parameters
    bank_filter = request.args.get('bank_filter', '').strip()
    sftp_filter = request.args.get('sftp_filter', '').strip()
    from_date_str = request.args.get('from_date', '').strip()
    to_date_str = request.args.get('to_date', '').strip()

    # Base query: show ALL statement logs for admin management
    # (Do not restrict by current_company_id to allow full management across companies)
    stmt_query = StatementLog.query

    # Apply filters
    if bank_filter:
        stmt_query = stmt_query.filter(StatementLog.bank_code == bank_filter)

    if sftp_filter == 'uploaded':
        stmt_query = stmt_query.filter(StatementLog.sftp_uploaded == True)
    elif sftp_filter == 'not_uploaded':
        stmt_query = stmt_query.filter(StatementLog.sftp_uploaded == False)
    elif sftp_filter == 'error':
        stmt_query = stmt_query.filter(
            StatementLog.sftp_uploaded == False,
            StatementLog.sftp_upload_message.isnot(None)
        )

    if from_date_str:
        try:
            from_date = datetime.strptime(from_date_str, '%Y-%m-%d')
            stmt_query = stmt_query.filter(StatementLog.processed_at >= from_date)
        except ValueError:
            pass

    if to_date_str:
        try:
            to_date = datetime.strptime(to_date_str, '%Y-%m-%d')
            # Add one day to include the entire end date
            to_date = to_date + timedelta(days=1)
            stmt_query = stmt_query.filter(StatementLog.processed_at < to_date)
        except ValueError:
            pass

    stmt_query = stmt_query.order_by(StatementLog.processed_at.desc())

    total = stmt_query.count()
    total_pages = max(1, math.ceil(total / per_page))
    if page > total_pages:
        page = total_pages
    offset = (page - 1) * per_page
    statement_logs = stmt_query.offset(offset).limit(per_page).all()

    stmt_pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': total_pages,
        'has_prev': page > 1,
        'has_next': page < total_pages,
    }

    # Recent Bank Logs with pagination (for "Lịch sử gần đây")
    logs_page = request.args.get('logs_page', type=int, default=1)
    logs_per_page = request.args.get('logs_per_page', type=int, default=10)
    if logs_page and logs_page < 1:
        logs_page = 1
    if logs_per_page and (logs_per_page < 1 or logs_per_page > 100):
        logs_per_page = 10

    logs_query = BankLog.query
    if current_company_id:
        logs_query = logs_query.filter(BankLog.company_id == current_company_id)
    logs_query = logs_query.order_by(BankLog.processed_at.desc())

    logs_total = logs_query.count()
    logs_total_pages = max(1, math.ceil(logs_total / logs_per_page))
    if logs_page > logs_total_pages:
        logs_page = logs_total_pages
    logs_offset = (logs_page - 1) * logs_per_page
    logs = logs_query.offset(logs_offset).limit(logs_per_page).all()

    logs_pagination = {
        'page': logs_page,
        'per_page': logs_per_page,
        'total': logs_total,
        'total_pages': logs_total_pages,
        'has_prev': logs_page > 1,
        'has_next': logs_page < logs_total_pages,
    }

    return render_template('admin_upload.html',
                         username=session.get('username'),
                         companies=companies,
                         current_company_id=current_company_id,
                         company_name=company_name,
                         statement_logs=statement_logs,
                         stmt_pagination=stmt_pagination,
                         logs=logs,
                         logs_pagination=logs_pagination)


@admin_bp.route('/admin/admin-upload', methods=['POST'])
def admin_process_upload():
    """Process file upload for admin - includes ZIP processing and MT940 generation"""
    if session.get('role') != 'admin':
        flash('Chỉ admin mới có quyền upload!', 'danger')
        return redirect(url_for('auth.login'))

    import shutil
    from werkzeug.utils import secure_filename
    from services.file_service import read_file_to_text, cleanup_file
    from services.detection_service import detect_bank_and_process
    from services.zip_service import safe_extract_zip
    from services.statement_service import parse_and_store_statement
    from models.statement_log import StatementLog
    from models.bank_log import BankLog

    user_id = session.get('user_id')
    company_id = session.get('company_id')

    # Validate user exists
    user = User.query.get(user_id)
    if not user:
        flash("User không tồn tại, vui lòng đăng nhập lại!", 'danger')
        return redirect(url_for('auth.logout'))

    if not company_id:
        flash("Vui lòng chọn công ty trước khi upload!", 'warning')
        return redirect(url_for('admin.admin_upload_page'))

    f = request.files.get("file")
    if not f:
        flash("Không tìm thấy file!", 'danger')
        return redirect(url_for('admin.admin_upload_page'))

    orig_name = secure_filename(f.filename)
    ext = orig_name.rsplit(".", 1)[-1].lower()

    from config import Config
    allowed_extensions = Config.ALLOWED_EXTENSIONS

    if ext not in allowed_extensions:
        flash("Định dạng file không được hỗ trợ!", 'danger')
        return redirect(url_for('admin.admin_upload_page'))

    upload_folder = Config.UPLOAD_FOLDER
    os.makedirs(upload_folder, exist_ok=True)
    saved_name = f"{uuid.uuid4().hex}.{ext}"
    saved_path = os.path.join(upload_folder, saved_name)
    f.save(saved_path)

    # track first parsed statement that is missing an account number so we can redirect
    missing_statement_log_id = None

    try:
        # If uploaded file is a ZIP archive, extract and process each allowed file inside
        if ext == 'zip':
            temp_dir = os.path.join(upload_folder, 'tmp', uuid.uuid4().hex)
            os.makedirs(temp_dir, exist_ok=True)
            # allowed extensions inside zip (exclude zip itself)
            allowed = set(allowed_extensions) - {'zip'}
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
                            failures.append(f"{orig_inner}: {parse_result.get('message', 'Không hợp lệ')}")
                        elif parse_result.get('status') == 'SUCCESS':
                            successes += 1
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
                        errors = parse_result.get('errors', [])
                        error_msg = parse_result.get('message', 'Mẫu sổ phụ không hợp lệ')
                        flash(error_msg, 'danger')
                        for err in errors[:5]:
                            flash(f"• {err}", 'warning')
                    elif parse_result.get('status') == 'SUCCESS':
                        flash('Sổ phụ đã được phân tích và MT940 sẵn sàng để tải xuống.', 'success')
                        sid = parse_result.get('statement_log_id')
                        if sid:
                            try:
                                stmt = StatementLog.query.filter_by(id=sid).first()
                                if stmt and not (stmt.accountno and str(stmt.accountno).strip()):
                                    cleanup_file(saved_path)
                                    return redirect(url_for('main.view_statement_detail', log_id=sid))
                            except Exception:
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

    return redirect(url_for('admin.admin_upload_page'))


@admin_bp.route('/admin/view-logs')
def view_logs():
    """View all bank logs with filtering and pagination"""
    if session.get('role') != 'admin':
        flash('Chỉ admin mới có quyền xem logs!', 'danger')
        return redirect(url_for('auth.login'))

    from models.company import Company
    from models.bank_log import BankLog
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


@admin_bp.route('/admin/admin-view-logs')
def admin_view_logs():
    """View all bank logs with filtering and pagination"""
    if session.get('role') != 'admin':
        flash('Chỉ admin mới có quyền xem logs!', 'danger')
        return redirect(url_for('auth.login'))

    from models.company import Company
    from models.bank_log import BankLog
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

    return render_template('admin_logs.html',
                         logs=logs,
                         pagination=pagination,
                         username=session.get('username'),
                         companies=companies,
                         current_company_id=current_company_id,
                         company_name=company_name)
