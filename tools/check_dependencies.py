import sys
import subprocess

REQUIRED_PACKAGES = [
    'flask',
    'flask-login',
    'flask-sqlalchemy',
    'flask-babel',
    'psycopg2-binary',
    'python-docx',
    'pandas',
    'openpyxl',
    'werkzeug',
    'pytest',
    'pytest-cov',
    'pytest-flask'
]

def check_and_install():
    """Kiểm tra và cài đặt packages thiếu"""
    missing = []

    print("🔍 Checking dependencies...")
    for package in REQUIRED_PACKAGES:
        try:
            # Try importing with underscore (flask_babel) if hyphen doesn't work
            pkg_import = package.replace('-', '_')
            __import__(pkg_import)
            print(f"  ✅ {package}")
        except ImportError:
            missing.append(package)
            print(f"  ❌ {package} - MISSING")

    if missing:
        print(f"\n📦 Installing {len(missing)} missing packages...")
        for pkg in missing:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
                print(f"  ✅ Installed {pkg}")
            except Exception as e:
                print(f"  ❌ Failed to install {pkg}: {e}")
                return False
        print("\n✅ All dependencies installed!")
    else:
        print("\n✅ All dependencies already installed!")

    return True

if __name__ == "__main__":
    success = check_and_install()
    if not success:
        print("\n❌ Some dependencies failed to install.")
        print("Try manually: pip install -r requirements.txt")
        sys.exit(1)
    sys.exit(0)
