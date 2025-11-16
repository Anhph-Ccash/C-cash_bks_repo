from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash

auth_bp = Blueprint('auth', __name__)

# Lazy import helper to avoid circular import at module import time
def _get_user_model():
	"""
	Lazy import User model to break circular imports between app.factory <-> routes.
	Call this inside request handlers or functions that run after app is created.
	"""
	try:
		# primary import path (models package at repo root)
		from models.user import User
	except Exception:
		# fallback if models exposes User at top-level
		from models import User
	return User

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            password = request.form.get('password')

            if not username or not password:
                return render_template('login.html', error="Vui lòng nhập đầy đủ thông tin")

            User = _get_user_model()
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
        except Exception as e:
            return render_template('login.html', error=f"Lỗi đăng nhập: {str(e)}")
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))

@auth_bp.route('/switch-company/<int:company_id>')
def switch_company(company_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    from app.models import Company, UserCompany
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

    # Determine where to redirect
    # Priority: 1) next parameter, 2) referrer analysis, 3) role-based default

    # Check for 'next' parameter in URL
    next_page = request.args.get('next')
    if next_page:
        print(f"DEBUG switch_company: Using next parameter = {next_page}")
        return redirect(next_page)

    # Analyze referrer
    referrer = request.referrer
    print(f"DEBUG switch_company: referrer = {referrer}, role = {session.get('role')}")

    if referrer:
        # Parse the referrer to determine which page to redirect to
        if '/admin/upload' in referrer or 'admin-upload' in referrer:
            print("DEBUG: Redirecting to admin_upload_page")
            return redirect(url_for('admin.admin_upload_page'))
        elif '/user/upload' in referrer or 'user-upload' in referrer:
            print("DEBUG: Redirecting to user_upload_page")
            return redirect(url_for('main.user_upload_page'))
        elif '/dashboard' in referrer or '/user' in referrer:
            print("DEBUG: Redirecting to user_dashboard")
            return redirect(url_for('main.user_dashboard'))
        elif '/admin' in referrer and session.get('role') == 'admin':
            print("DEBUG: Redirecting to admin page")
            return redirect(url_for('admin.admin'))
        else:
            # Default: try to go back to referrer
            print("DEBUG: Redirecting to referrer directly")
            return redirect(referrer)

    # If no referrer, redirect based on role
    print("DEBUG: No referrer, using role-based redirect")
    if session.get('role') == 'admin':
        return redirect(url_for('admin.admin_upload_page'))
    else:
        return redirect(url_for('main.user_dashboard'))
