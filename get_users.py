#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Get all usernames from the users table"""

from app import create_app
from extensions import db
from models.user import User

app = create_app()

with app.app_context():
    users = User.query.all()
    print('\nDanh sách Users:')
    print('=' * 70)
    for user in users:
        print(f'ID: {user.id} | Username: {user.username} | Email: {user.email} | Role: {user.role}')
    print('=' * 70)
    print(f'Total: {len(users)} users\n')
