# AI Development Guide for Flask User Management System

## Project Architecture

This is a Flask web application for managing bank file uploads and processing, with these key components:

### Core Components
- **Application Factory**: Uses Flask factory pattern in `app.py` for modular initialization
- **Blueprint Structure**: Modular features split into blueprints (`upload`, `bank_config`, `bank_log`)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: Flask-Login based user system with role-based access

### Key Workflows

1. **File Upload & Processing Pipeline**:
   ```
   Upload (routes.py) -> File Service -> Detection Service -> Database
   ```
   See `app/blueprints/upload/routes.py` for the pattern.

2. **Bank Configuration Management**:
   - Configs stored in database (see `app/models/bank_config.py`)
   - API endpoints in `bank_config` blueprint

### Development Guidelines

1. **File Structure**:
   - Business logic in `app/services/`
   - Database models in `app/models/`
   - Route handlers in blueprint directories
   - File processors in `app/readers/`

2. **Error Handling Pattern**:
   ```python
   try:
       # Operation
       db.session.commit()
   except Exception as e:
       db.session.rollback()
       return jsonify({"status": "FAILED", "message": str(e)}), 500
   ```

3. **File Upload Convention**:
   - Temporary files in `uploads/` directory
   - Supported formats: xls, xlsx, csv, mt940, txt
   - Always use `cleanup_file()` after processing

### Environment Setup

1. **Database**:
   - PostgreSQL required
   - Connection string in `config.py`
   - Default port: 5432

2. **Application**:
   - Runs on port 5001 in debug mode
   - Uses template folder at root level

### Security Considerations

1. **File Handling**:
   - Always use `secure_filename()`
   - Validate file extensions
   - Clean up uploaded files

2. **Authentication**:
   - Role-based access control
   - Password hashing enforced
   - Session management via Flask-Login

## Common Tasks

1. **Adding New File Format**:
   1. Update `ALLOWED_EXTENSIONS` in `config.py`
   2. Add reader in `app/readers/`
   3. Update detection service logic

2. **Creating New Blueprint**:
   1. Create directory in `app/blueprints/`
   2. Include `__init__.py` and `routes.py`
   3. Register in `app.py`