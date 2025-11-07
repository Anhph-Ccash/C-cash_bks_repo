from flask import Blueprint, render_template, session, redirect, url_for
from functools import wraps

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        if session.get('role') != 'admin':
            return redirect(url_for('main.user_dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/admin')
@admin_required
def dashboard():
    return render_template('admin.html', username=session.get('username'))