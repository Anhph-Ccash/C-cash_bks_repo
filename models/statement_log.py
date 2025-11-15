from extensions import db
from sqlalchemy.sql import func

class StatementLog(db.Model):
    __tablename__ = 'statement_log'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id', ondelete='CASCADE'), nullable=True)
    bank_code = db.Column(db.String, nullable=True)
    filename = db.Column(db.String, nullable=False)
    original_filename = db.Column(db.String, nullable=True)
    status = db.Column(db.String, nullable=False)
    message = db.Column(db.Text, nullable=True)

    # Header fields
    accountno = db.Column(db.String, nullable=True)
    currency = db.Column(db.String, nullable=True)
    opening_balance = db.Column(db.String, nullable=True)
    closing_balance = db.Column(db.String, nullable=True)

    # Details stored as JSON array of objects
    details = db.Column(db.JSON, nullable=True)

    # Generated MT940 filename (relative to UPLOAD_FOLDER)
    mt940_filename = db.Column(db.String, nullable=True)

    # SFTP upload tracking
    sftp_uploaded = db.Column(db.Boolean, default=False)
    sftp_uploaded_at = db.Column(db.TIMESTAMP, nullable=True)
    sftp_remote_path = db.Column(db.String(500), nullable=True)
    sftp_upload_message = db.Column(db.Text, nullable=True)

    processed_at = db.Column(db.TIMESTAMP, server_default=func.now())

    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='statement_logs')
    company = db.relationship('Company', back_populates='statement_logs')
