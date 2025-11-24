#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Create new admin user"""

from app import create_app
from extensions import db
from models.user import User
from models.user_company import UserCompany

app = create_app()

with app.app_context():
    # Check if user already exists
    existing_user = User.query.filter_by(email='sgp.hoanganh@gmail.com').first()
    if existing_user:
        print(f'⚠️  User với email này đã tồn tại')
        print(f'   ID: {existing_user.id}')
        print(f'   Username: {existing_user.username}')
        print(f'   Email: {existing_user.email}')
        print(f'   Role: {existing_user.role}')
    else:
        # Create new user
        new_user = User(
            username='anh.pham',
            email='sgp.hoanganh@gmail.com',
            role='admin'
        )
        new_user.set_password('CCash@2025')

        db.session.add(new_user)
        db.session.flush()  # Get the user ID

        # Assign to company
        user_company = UserCompany(
            user_id=new_user.id,
            company_id=1,
            role='admin'
        )
        db.session.add(user_company)
        db.session.commit()

        print('✅ User tạo thành công!')
        print(f'   ID: {new_user.id}')
        print(f'   Username: {new_user.username}')
        print(f'   Email: {new_user.email}')
        print(f'   Role: {new_user.role}')
        print(f'   Company ID: 1')
        print(f'   Password: CCash@2025')
