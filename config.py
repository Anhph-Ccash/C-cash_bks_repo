import os
from urllib.parse import quote_plus

class Config:
    # Read secrets from environment for production (Render will provide DATABASE_URL)
    SECRET_KEY = os.environ.get('SECRET_KEY', 'admin@123')

    # Database configuration
    # Để sử dụng local database, uncomment dòng dưới và comment dòng remote
    # SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:11223344@localhost:5432/FlaskWebPostgreSQL'
    # SQLALCHEMY_DATABASE_URI = os.environ.get(
    #     'DATABASE_URL',
    #     'postgresql://postgres:11223344@localhost:5432/FlaskWebPostgreSQL'
    # )
    # Remote database (Render)
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'postgresql://flaskwebpostgresql_user:nrDeXdaJQ2GA9Bv04ISC2rdNpI7EKhYr@dpg-d47l9824d50c7388ofsg-a.singapore-postgres.render.com/flaskwebpostgresql'
    )

    # AWS RDS Database - Password must be URL encoded due to special characters

    # _DB_PASSWORD = quote_plus('HX>hH$!9qz<bLh#x(hp$Gl1ST)q<')
    # _DB_HOST = 'flask-database.cdcieg2y8fcu.ap-southeast-1.rds.amazonaws.com'
    # _DB_NAME = 'postgres'

    # SQLALCHEMY_DATABASE_URI = os.environ.get(
    #     'DATABASE_URL',
    #     f'postgresql://postgres:{_DB_PASSWORD}@{_DB_HOST}:5432/{_DB_NAME}'
    # )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Connection pool settings to handle connection issues
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,  # Verify connections before using them
        'pool_recycle': 300,    # Recycle connections after 5 minutes
        'pool_size': 10,        # Maximum number of connections
        'max_overflow': 20,     # Maximum overflow connections
        'pool_timeout': 30,     # Timeout for getting connection from pool
    }

    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
    ALLOWED_EXTENSIONS = {'xls', 'xlsx', 'csv', 'mt940', 'txt', 'zip'}
