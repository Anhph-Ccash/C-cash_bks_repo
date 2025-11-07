import os

class Config:
    SECRET_KEY = "admin123"
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:11223344@localhost:5432/FlaskWebPostgreSQL"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
    ALLOWED_EXTENSIONS = {'xls', 'xlsx', 'csv', 'mt940', 'txt', 'zip'}
    