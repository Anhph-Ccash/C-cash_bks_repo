from extensions import db
from datetime import datetime

class BankConfig(db.Model):
    __tablename__ = 'bank_config'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id', ondelete='CASCADE'), nullable=True)
    bank_code = db.Column(db.String, nullable=False)
    bank_name = db.Column(db.String, nullable=True)
    keywords = db.Column(db.ARRAY(db.String), default=[])
    scan_ranges = db.Column(db.JSON, default=[])
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    company = db.relationship('Company', back_populates='bank_configs')

    __table_args__ = (
        db.UniqueConstraint('company_id', 'bank_code', name='unique_company_bank'),
    )
