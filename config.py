import os

class Config:
    # Read secrets from environment for production (Render will provide DATABASE_URL)
    SECRET_KEY = os.environ.get('SECRET_KEY', 'admin123')
    # Use DATABASE_URL if provided, otherwise fall back to local dev DB
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'postgresql://flaskwebpostgresql_user:nrDeXdaJQ2GA9Bv04ISC2rdNpI7EKhYr@dpg-d47l9824d50c7388ofsg-a.singapore-postgres.render.com/flaskwebpostgresql'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
    ALLOWED_EXTENSIONS = {'xls', 'xlsx', 'csv', 'mt940', 'txt', 'zip'}
    
