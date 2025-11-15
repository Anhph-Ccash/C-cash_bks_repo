from extensions import db
from sqlalchemy.sql import func

class BankLog(db.Model):
    __tablename__ = 'bank_log'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id', ondelete='CASCADE'), nullable=True)
    bank_code = db.Column(db.String, nullable=True)
    filename = db.Column(db.String, nullable=False)
    original_filename = db.Column(db.String, nullable=True)
    status = db.Column(db.String, nullable=False)
    message = db.Column(db.Text, nullable=True)
    detected_keywords = db.Column(db.ARRAY(db.String), default=[])
    processed_at = db.Column(db.TIMESTAMP, server_default=func.now())

    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='bank_logs')
    company = db.relationship('Company', back_populates='bank_logs')
