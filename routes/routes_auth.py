from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash
from models import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            
            # Get user's companies
            companies = user.get_companies()
            if companies:
                # If user has companies, set the first one as default
                session['company_id'] = companies[0].id
                session['company_name'] = companies[0].name
            
            flash('Đăng nhập thành công!', 'success')
            return redirect(url_for('admin.admin')) if user.role == 'admin' else redirect(url_for('main.user_dashboard'))
        else:
            return render_template('login.html', error="Sai tên đăng nhập hoặc mật khẩu")
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))

@auth_bp.route('/switch-company/<int:company_id>')
def switch_company(company_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    from models import User, Company, UserCompany
    user = User.query.get(session['user_id'])
    
    # Admin can access all companies, regular users need UserCompany permission
    if session.get('role') == 'admin':
        company = Company.query.get(company_id)
        if company and company.is_active:
            session['company_id'] = company.id
            session['company_name'] = company.name
            flash(f'Đã chuyển sang công ty: {company.name}', 'success')
        else:
            flash('Công ty không tồn tại hoặc không hoạt động!', 'danger')
    else:
        # Check if user has access to this company
        user_company = UserCompany.query.filter_by(
            user_id=user.id,
            company_id=company_id
        ).first()
        
        if user_company:
            company = Company.query.get(company_id)
            if company and company.is_active:
                session['company_id'] = company.id
                session['company_name'] = company.name
                flash(f'Đã chuyển sang công ty: {company.name}', 'success')
        else:
            flash('Bạn không có quyền truy cập công ty này!', 'danger')
    
    return redirect(request.referrer or url_for('main.user_dashboard'))