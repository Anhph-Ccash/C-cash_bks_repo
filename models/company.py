from extensions import db

class Company(db.Model):
    __tablename__ = 'company'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text)
    tax_code = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)

     # Thông tin SFTP
    sftp_host = db.Column(db.String(255))
    sftp_port = db.Column(db.Integer, default=22)
    sftp_username = db.Column(db.String(255))
    sftp_password = db.Column(db.String(255))
    sftp_remote_path = db.Column(db.String(255))
    sftp_private_key_path = db.Column(db.String(255))

    # Relationships
    user_companies = db.relationship('UserCompany', back_populates='company', cascade='all, delete-orphan')
    bank_configs = db.relationship('BankConfig', back_populates='company', cascade='all, delete-orphan')
    bank_logs = db.relationship('BankLog', back_populates='company', cascade='all, delete-orphan')
    statement_logs = db.relationship('StatementLog', back_populates='company', cascade='all, delete-orphan')
