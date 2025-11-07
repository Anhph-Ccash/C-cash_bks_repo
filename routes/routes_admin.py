from flask import Blueprint, render_template, request, redirect, url_for, session
from extensions import db
from models import User
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import SQLAlchemyError

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin')
def admin():
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))
    
    from models.company import Company
    
    # Get all users and companies
    users = User.query.all()
    companies = Company.query.filter_by(is_active=True).all()

    # Also provide bank configs and statement configs ordered A-Z by bank_code
    from models.bank_config import BankConfig
    from models.bank_statement_config import BankStatementConfig
    bank_configs = BankConfig.query.order_by(BankConfig.bank_code.asc()).all()
    statement_configs = BankStatementConfig.query.order_by(BankStatementConfig.bank_code.asc()).all()
    
    # Get current company from session (admin can also switch companies)
    current_company_id = session.get('company_id')
    company_name = session.get('company_name')
    
    return render_template('admin.html', 
                         users=users, 
                         username=session.get('username'),
                         companies=companies,
                         current_company_id=current_company_id,
                         company_name=company_name,
                         bank_configs=bank_configs,
                         statement_configs=statement_configs)

@admin_bp.route('/add', methods=['POST'])
def add_user():
    if session.get('role') != 'admin':
        return "Bạn không có quyền thêm user", 403
    
    from models.user_company import UserCompany
    
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    role = request.form.get('role', 'user')
    company_ids = request.form.getlist('company_ids[]')  # Multiple companies
    
    try:
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
        return redirect(url_for('admin.admin'))
    except SQLAlchemyError as e:
        db.session.rollback()
        return str(e), 500

@admin_bp.route('/update/<int:user_id>', methods=['POST'])
def update_user(user_id):
    if session.get('role') != 'admin':
        return "Bạn không có quyền cập nhật", 403
    user = User.query.get(user_id)
    if not user:
        return "Không tìm thấy user", 404
    user.username = request.form['username']
    user.email = request.form['email']
    db.session.commit()
    return redirect(url_for('admin.admin'))

@admin_bp.route('/delete/<int:user_id>')
def delete_user(user_id):
    if session.get('role') != 'admin':
        return "Bạn không có quyền xóa", 403
    user = User.query.get(user_id)
    if not user:
        return "Không tìm thấy user", 404
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('admin.admin'))

# Company Management Routes
@admin_bp.route('/company/add', methods=['POST'])
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
        return redirect(url_for('admin.admin'))
    except SQLAlchemyError as e:
        db.session.rollback()
        return str(e), 500

@admin_bp.route('/company/update/<int:company_id>', methods=['POST'])
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
        return redirect(url_for('admin.admin'))
    except SQLAlchemyError as e:
        db.session.rollback()
        return str(e), 500

@admin_bp.route('/company/delete/<int:company_id>')
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
        return redirect(url_for('admin.admin'))
    except SQLAlchemyError as e:
        db.session.rollback()
        return str(e), 500

