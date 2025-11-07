from extensions import db, login_manager
from flask_login import UserMixin
from werkzeug.security import check_password_hash

class User(db.Model, UserMixin):
	__tablename__ = 'users'
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(80), unique=True, nullable=False)
	email = db.Column(db.String(120), unique=True, nullable=False)
	password_hash = db.Column(db.String(128), nullable=False)
	role = db.Column(db.String(10), default='user')
	
	# Relationships
	user_companies = db.relationship('UserCompany', back_populates='user', cascade='all, delete-orphan')

	def check_password(self, password):
		return check_password_hash(self.password_hash, password)
	
	def get_companies(self):
		"""Get all companies this user belongs to"""
		from .user_company import UserCompany
		from .company import Company
		return db.session.query(Company).join(UserCompany).filter(
			UserCompany.user_id == self.id,
			Company.is_active == True
		).all()


@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))

# Import models from submodules
from .bank_config import BankConfig
from .bank_log import BankLog
from .company import Company
from .user_company import UserCompany

__all__ = ['User', 'BankConfig', 'BankLog', 'Company', 'UserCompany']


from .bank_config import BankConfig
from .bank_log import BankLog