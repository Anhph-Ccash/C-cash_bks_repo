import sys
import subprocess
import os

def install_requirements():
    """Cài đặt tất cả dependencies cho development và testing"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    print("=" * 70)
    print("📦 INSTALLING DEPENDENCIES")
    print("=" * 70)

    # Cài đặt requirements chính
    req_file = os.path.join(project_root, "requirements.txt")
    if os.path.exists(req_file):
        print(f"\n✅ Installing main requirements from: {req_file}")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", req_file])
            print("✅ Main requirements installed successfully!")
        except Exception as e:
            print(f"❌ Error installing main requirements: {e}")
            return False

    # Cài đặt dev requirements
    dev_req_file = os.path.join(project_root, "requirements-dev.txt")
    if os.path.exists(dev_req_file):
        print(f"\n✅ Installing dev requirements from: {dev_req_file}")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", dev_req_file])
            print("✅ Dev requirements installed successfully!")
        except Exception as e:
            print(f"❌ Error installing dev requirements: {e}")
            return False

    print("\n" + "=" * 70)
    print("✅ ALL DEPENDENCIES INSTALLED SUCCESSFULLY!")
    print("=" * 70)
    return True

if __name__ == "__main__":
    success = install_requirements()
    sys.exit(0 if success else 1)
