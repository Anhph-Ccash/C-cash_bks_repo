from extensions import db
from datetime import datetime

class BankStatementConfig(db.Model):
    __tablename__ = 'bank_statement_config'

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id', ondelete='CASCADE'), nullable=False)
    bank_code = db.Column(db.String, nullable=False)
    keywords = db.Column(db.ARRAY(db.String), nullable=False, default=[])
    col_keyword = db.Column(db.String, nullable=True)
    col_value = db.Column(db.String, nullable=True)
    row_start = db.Column(db.Integer, nullable=True)
    row_end = db.Column(db.Integer, nullable=True)
    identify_info = db.Column(db.Text, nullable=False, default='')
    cell_format = db.Column(db.String, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    company = db.relationship('Company', backref='statement_configs')

    __table_args__ = (
        db.UniqueConstraint('company_id', 'bank_code', 'identify_info', name='unique_company_statement_config_field'),
    )
