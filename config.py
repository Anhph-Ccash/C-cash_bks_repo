import os

class Config:
    # Read secrets from environment for production (Render will provide DATABASE_URL)
    SECRET_KEY = os.environ.get('SECRET_KEY', 'admin@123')

    # Database configuration
    # Production: Use DATABASE_URL environment variable (set on Render Dashboard)
    # Local development: Falls back to local PostgreSQL
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'postgresql://postgres:11223344@localhost:5432/FlaskWebPostgreSQL'
    )

    # Ensure we have a valid database URL
    if not SQLALCHEMY_DATABASE_URI:
        raise RuntimeError(
            "DATABASE_URL environment variable not set. "
            "Please set DATABASE_URL on Render Dashboard or use local PostgreSQL."
        )

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
