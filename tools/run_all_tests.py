import sys
import subprocess
import os
import importlib

def ensure_pytest_installed():
    """Kiểm tra và cài đặt pytest, pytest-cov nếu chưa có"""
    try:
        import pytest
        import pytest_cov
    except ImportError:
        print("📦 Đang cài đặt pytest và pytest-cov...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pytest", "pytest-cov"])
            print("✅ Cài đặt thành công!")
        except Exception as e:
            print(f"❌ Lỗi cài đặt: {e}")
            print(f"Chạy thủ công: {sys.executable} -m pip install pytest pytest-cov")
            sys.exit(1)

def ensure_dependencies():
    """Kiểm tra và cài đặt dependencies trước khi chạy tests"""
    print("🔍 Checking dependencies...")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    check_deps_script = os.path.join(script_dir, 'check_dependencies.py')

    try:
        result = subprocess.run([sys.executable, check_deps_script], check=False)
        if result.returncode != 0:
            print("❌ Dependency check failed. Please install manually:")
            print(f"   {sys.executable} -m pip install flask-babel pytest pytest-cov")
            return False
        return True
    except Exception as e:
        print(f"⚠️ Could not run dependency check: {e}")
        print("Continuing with tests anyway...")
        return True

def ensure_runtime_deps():
    """Đảm bảo các runtime deps tối thiểu để import modules trong tests."""
    def _ensure(import_name, pip_name):
        try:
            importlib.import_module(import_name)
            return
        except ImportError:
            print(f"📦 Thiếu '{pip_name}', đang cài đặt...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name])
                print(f"✅ Đã cài {pip_name}")
            except Exception as e:
                print(f"❌ Không thể cài {pip_name}: {e}")
                print(f"Vui lòng chạy thủ công: {sys.executable} -m pip install {pip_name}")
                sys.exit(1)
    # Tối thiểu cần cho import chain: flask-babel
    _ensure("flask_babel", "flask-babel")

def run_tests():
    """Chạy toàn bộ unit tests với coverage"""
    # Đảm bảo đang ở thư mục root của project
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)

    print("=" * 70)
    print("🧪 CHẠY TOÀN BỘ UNIT TESTS")
    print("=" * 70)
    print(f"📂 Thư mục dự án: {project_root}")
    print(f"📂 Thư mục tests: {os.path.join(project_root, 'tests')}")
    print("=" * 70)

    # Chạy pytest với coverage
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",                          # verbose
        "--tb=short",                  # traceback ngắn gọn
        "--cov=services",              # coverage cho services
        "--cov=models",                # coverage cho models
        "--cov=blueprints",            # coverage cho blueprints
        "--cov-report=term-missing",   # hiển thị dòng code thiếu test
        "--cov-report=html",           # tạo HTML report
        "-s"                           # hiển thị print statements
    ]
    # Thiết lập PYTHONPATH để import được 'services', 'models', ...
    env = os.environ.copy()
    env["PYTHONPATH"] = project_root + os.pathsep + env.get("PYTHONPATH", "")

    try:
        result = subprocess.run(cmd, check=False, env=env)

        print("\n" + "=" * 70)
        if result.returncode == 0:
            print("✅ TẤT CẢ TESTS ĐÃ PASS!")
        else:
            print("❌ CÓ TESTS BỊ FAIL!")
        print("=" * 70)

        print("\n📊 Coverage report đã được tạo tại: htmlcov/index.html")
        print("   Mở file này bằng trình duyệt để xem chi tiết coverage")

        return result.returncode

    except Exception as e:
        print(f"\n❌ Lỗi khi chạy tests: {e}")
        return 1

def run_specific_test(test_path):
    """Chạy một test cụ thể"""
    print(f"🎯 Chạy test: {test_path}")
    cmd = [sys.executable, "-m", "pytest", test_path, "-v", "-s"]
    # Thiết lập PYTHONPATH tương tự như run_tests
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env = os.environ.copy()
    env["PYTHONPATH"] = project_root + os.pathsep + env.get("PYTHONPATH", "")
    result = subprocess.run(cmd, check=False, env=env)
    return result.returncode

if __name__ == "__main__":
    # Kiểm tra dependencies trước
    if not ensure_dependencies():
        sys.exit(1)

    ensure_pytest_installed()
    ensure_runtime_deps()  # mới: đảm bảo flask-babel có sẵn để tránh lỗi import

    # Nếu có argument, chạy test cụ thể
    if len(sys.argv) > 1:
        test_path = sys.argv[1]
        exit_code = run_specific_test(test_path)
    else:
        # Chạy toàn bộ tests
        exit_code = run_tests()

    sys.exit(exit_code)
