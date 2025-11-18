# 🧪 Hướng dẫn chạy Unit Tests

## Cài đặt dependencies

```bash
# Kích hoạt virtual environment
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Cách 1: Cài đặt tự động (khuyến nghị)
python tools\check_dependencies.py

# Cách 2: Cài đặt thủ công
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Cách 3: Cài đặt nhanh các packages quan trọng
pip install flask-babel pytest pytest-cov pytest-flask
```

## Chạy toàn bộ tests

### Cách 1: Dùng script Python (tự động kiểm tra dependencies)
```bash
python tools\run_all_tests.py
```

### Cách 2: Dùng pytest trực tiếp
```bash
# Chạy tất cả tests
pytest tests/ -v

# Chạy với coverage
pytest tests/ -v --cov=services --cov=models --cov-report=html
```

## Chạy test cụ thể

```bash
# Chạy một file test
pytest tests/test_statement_service.py -v

# Chạy một test function cụ thể
pytest tests/test_statement_service.py::test_build_mt940_basic -v

# Chạy test với keyword
pytest tests/ -k "mt940" -v
```

## Xem Coverage Report

Sau khi chạy tests với coverage, mở file:
```
htmlcov/index.html
```

## Cấu trúc thư mục tests

```
tests/
├── test_statement_service.py    # Tests cho statement service
├── test_bank_config.py           # Tests cho bank config
├── test_file_detection.py        # Tests cho file detection
└── ...
```

## Viết tests mới

Tạo file test mới trong thư mục `tests/` với prefix `test_`:

```python
# filepath: tests/test_example.py
import pytest

def test_example_function():
    # Arrange
    input_data = "test"

    # Act
    result = some_function(input_data)

    # Assert
    assert result == expected_output
```

## CI/CD

Tests sẽ tự động chạy khi:
- Push code lên GitHub
- Tạo Pull Request
- Merge vào branch main

## Troubleshooting

### Lỗi: ModuleNotFoundError
```bash
# Đảm bảo PYTHONPATH được set
set PYTHONPATH=e:\C-cash_bks_repo  # Windows
export PYTHONPATH=e:\C-cash_bks_repo  # Linux/Mac
```

### Lỗi: Database connection
- Đảm bảo PostgreSQL đang chạy
- Kiểm tra connection string trong config.py
- Tạo test database riêng nếu cần
