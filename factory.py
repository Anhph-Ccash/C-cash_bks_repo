from flask import Flask, render_template, jsonify, request, session, redirect, url_for, current_app
from config import Config
from extensions import db, login_manager, csrf, babel
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from flask_wtf.csrf import generate_csrf


def create_app():
    app = Flask(__name__, template_folder="templates")
    app.config.from_object(Config)
    # i18n defaults
    app.config.setdefault("LANGUAGES", ["vi", "en"])  # supported languages
    app.config.setdefault("BABEL_DEFAULT_LOCALE", "vi")
    app.config.setdefault("BABEL_DEFAULT_TIMEZONE", "Asia/Ho_Chi_Minh")
    # Ensure csrf_token() is available in Jinja templates
    app.jinja_env.globals['csrf_token'] = generate_csrf

    # Locale selector
    def select_locale() -> str:
        lang = session.get('lang')
        if lang in app.config.get('LANGUAGES', []):
            return lang
        # Default to Vietnamese regardless of browser settings
        return app.config.get('BABEL_DEFAULT_LOCALE', 'vi')

    babel.init_app(app, locale_selector=select_locale)

    # Expose helper to templates
    @app.context_processor
    def inject_i18n():
        return {
            'current_lang': session.get('lang', app.config.get('BABEL_DEFAULT_LOCALE', 'vi')),
            'languages': app.config.get('LANGUAGES', ['vi', 'en'])
        }

    # Register blueprint packages (API and UI)
    from blueprints.upload import upload_bp
    from blueprints.bank_config import bank_config_bp
    from blueprints.bank_log import bank_log_bp

    # auth/admin/main are in `app.routes` as module-based blueprints
    from routes.routes_auth import auth_bp
    from routes.routes_admin import admin_bp
    from routes.routes_main import main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(main_bp)

    app.register_blueprint(upload_bp, url_prefix="/admin/upload")
    app.register_blueprint(bank_config_bp, url_prefix="/config")
    app.register_blueprint(bank_log_bp, url_prefix="/log")

    # Simple route to switch language
    @app.route('/i18n/set-lang/<lang>')
    def set_language(lang: str):
        if lang not in current_app.config.get('LANGUAGES', []):
            lang = current_app.config.get('BABEL_DEFAULT_LOCALE', 'vi')
        session['lang'] = lang
        next_url = request.args.get('next') or request.referrer or url_for('main.user_dashboard')
        return redirect(next_url)

    # Initialize login manager
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Vui lòng đăng nhập trước khi truy cập trang này.'

    # User loader callback for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        try:
            from models.user import User
            return User.query.get(int(user_id))
        except Exception:
            return None

    # Error handlers
    @app.errorhandler(OperationalError)
    def handle_db_error(error):
        """Handle database connection errors"""
        db.session.rollback()
        app.logger.error(f"Database error: {error}")
        return render_template('error.html',
                             error_title="Lỗi kết nối Database",
                             error_message="Không thể kết nối đến database. Vui lòng thử lại sau."), 500

    @app.errorhandler(500)
    def handle_500(error):
        """Handle internal server errors"""
        db.session.rollback()
        return render_template('error.html',
                             error_title="Lỗi Server",
                             error_message="Đã xảy ra lỗi. Vui lòng thử lại sau."), 500

    # create DB tables if necessary and seed default admin user
    with app.app_context():
        # initialize extensions (db, login, babel, csrf, ...)
        db.init_app(app)
        csrf.init_app(app)

        # ===== new: ensure admin user creation/check happens inside app context =====
        try:
            # Lazy import User model to avoid circular imports
            from models.user import User
            # Only attempt DB query if db is configured
            try:
                existing = User.query.filter_by(username='admin').first()
            except Exception as _qerr:
                # DB not ready or migration not run yet; skip creating admin for now
                app.logger.warning(f"Skipping admin creation - DB not ready: {_qerr}")
                existing = None

            if not existing:
                # Create default admin user safely if model supports it
                admin = User(username='admin', email='admin@example.com', role='admin')
                # try to set password via helper if available, else set password_hash
                if hasattr(admin, "set_password"):
                    try:
                        admin.set_password("ChangeMe123!")  # note: instruct to change after first login
                    except Exception:
                        from werkzeug.security import generate_password_hash
                        admin.password_hash = generate_password_hash("ChangeMe123!")
                else:
                    from werkzeug.security import generate_password_hash
                    admin.password_hash = generate_password_hash("ChangeMe123!")
                try:
                    db.session.add(admin)
                    db.session.commit()
                    app.logger.info("Default admin user created (username=admin). Please change password immediately.")
                except Exception as e:
                    db.session.rollback()
                    app.logger.warning(f"Could not create default admin user: {e}")
        except Exception as e:
            # If model import fails or other unexpected error, log and continue startup
            app.logger.warning(f"Admin-check skipped due to import/error: {e}")
        # ===== end admin check =====

    return app


__all__ = ["create_app"]
