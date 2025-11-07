from flask import Flask, render_template
from config import Config
from extensions import db, login_manager
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import SQLAlchemyError


def create_app():
    app = Flask(__name__, template_folder="templates")
    app.config.from_object(Config)
    db.init_app(app)
    login_manager.init_app(app)

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

    app.register_blueprint(upload_bp, url_prefix="/upload")
    app.register_blueprint(bank_config_bp, url_prefix="/config")
    app.register_blueprint(bank_log_bp, url_prefix="/log")

    # login settings
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Vui lòng đăng nhập trước khi truy cập trang này.'

    # create DB tables if necessary and seed default admin user
    with app.app_context():
        from models import User  # ensure models are imported
        db.create_all()
        try:
            if not User.query.filter_by(username='admin').first():
                admin = User(username='admin', email='admin@example.com',
                             password_hash=generate_password_hash('admin123'),
                             role='admin')
                db.session.add(admin)
                db.session.commit()
                print("✅ Đã tạo admin mặc định.")
        except SQLAlchemyError as e:
            db.session.rollback()
            # Log but don't crash app init
            print("⚠️ Lỗi khi tạo admin mặc định:", e)

    return app


__all__ = ["create_app"]
