from extensions import db
from sqlalchemy.sql import func

class UserCompany(db.Model):
    __tablename__ = 'user_company'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id', ondelete='CASCADE'), nullable=False)
    role = db.Column(db.String(50))  # admin, staff, viewer, etc.
    created_at = db.Column(db.TIMESTAMP, server_default=func.now())
    
    # Relationships
    user = db.relationship('User', back_populates='user_companies')
    company = db.relationship('Company', back_populates='user_companies')
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'company_id', name='unique_user_company'),
    )
