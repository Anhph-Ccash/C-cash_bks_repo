import sys
import os
import subprocess

# Wrapper so you can run: py generate_user_guide.py  (from repo root)
# It will execute tools/generate_user_guide.py with the same Python interpreter.

def main():
    repo_root = os.path.dirname(os.path.abspath(__file__))
    tools_script = os.path.join(repo_root, "tools", "generate_user_guide.py")
    if not os.path.exists(tools_script):
        print("Error: tools/generate_user_guide.py not found. Expected at:", tools_script)
        sys.exit(1)

    cmd = [sys.executable, tools_script] + sys.argv[1:]
    try:
        rc = subprocess.call(cmd)
        sys.exit(rc)
    except KeyboardInterrupt:
        print("Interrupted")
        sys.exit(1)
    except Exception as e:
        print("Failed to run tools script:", e)
        sys.exit(1)

if __name__ == "__main__":
    main()
