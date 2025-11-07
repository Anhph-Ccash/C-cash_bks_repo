from extensions import db

class Company(db.Model):
    __tablename__ = 'company'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text)
    tax_code = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    user_companies = db.relationship('UserCompany', back_populates='company', cascade='all, delete-orphan')
    bank_configs = db.relationship('BankConfig', back_populates='company', cascade='all, delete-orphan')
    bank_logs = db.relationship('BankLog', back_populates='company', cascade='all, delete-orphan')
    statement_logs = db.relationship('StatementLog', back_populates='company', cascade='all, delete-orphan')
