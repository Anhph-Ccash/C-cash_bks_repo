from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False, unique=True)
    email = db.Column(db.String, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    role = db.Column(db.String, nullable=True, default='user')  # admin, user

    # Relationships
    user_companies = db.relationship('UserCompany', back_populates='user', cascade='all, delete-orphan')

    def set_password(self, password):
        """Hash and store password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if provided password matches stored hash"""
        return check_password_hash(self.password_hash, password)

    def get_companies(self):
        """Get all companies this user has access to"""
        from models.company import Company
        return [uc.company for uc in self.user_companies if uc.company.is_active]

    def has_company_access(self, company_id):
        """Check if user has access to a specific company"""
        return any(uc.company_id == company_id for uc in self.user_companies)

    def get_role_for_company(self, company_id):
        """Get user's role for a specific company"""
        for uc in self.user_companies:
            if uc.company_id == company_id:
                return uc.role
        return None

    def __repr__(self):
        return f'<User {self.username}>'
