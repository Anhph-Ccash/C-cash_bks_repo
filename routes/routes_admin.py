from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from extensions import db
from models import User
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import SQLAlchemyError

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin')
def admin():
    """Redirect to users page by default"""
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/admin/users')
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

@admin_bp.route('/admin/companies')
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

@admin_bp.route('/admin/bank-configs')
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

@admin_bp.route('/admin/statement-configs')
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
    
    stmt_query = stmt_query.order_by(BankStatementConfig.bank_code.asc())
    
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
        return "Bạn không có quyền thêm company", 403
    
    from models.company import Company
    
    name = request.form['name']
    address = request.form.get('address', '')
    tax_code = request.form.get('tax_code', '')
    
    try:
        company = Company(name=name, address=address, tax_code=tax_code, is_active=True)
        db.session.add(company)
        db.session.commit()
        return redirect(url_for('admin.manage_companies'))
    except SQLAlchemyError as e:
        db.session.rollback()
        return str(e), 500

@admin_bp.route('/admin/company/update/<int:company_id>', methods=['POST'])
def update_company(company_id):
    if session.get('role') != 'admin':
        return "Bạn không có quyền cập nhật", 403
    
    from models.company import Company
    
    company = Company.query.get(company_id)
    if not company:
        return "Không tìm thấy company", 404
    
    company.name = request.form['name']
    company.address = request.form.get('address', '')
    company.tax_code = request.form.get('tax_code', '')
    
    try:
        db.session.commit()
        return redirect(url_for('admin.manage_companies'))
    except SQLAlchemyError as e:
        db.session.rollback()
        return str(e), 500

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

