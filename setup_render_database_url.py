#!/usr/bin/env python
"""
Script để setup DATABASE_URL environment variable trên Render.com
Yêu cầu: Render API token

Cách sử dụng:
  python setup_render_database_url.py --token YOUR_RENDER_API_TOKEN --service-id YOUR_SERVICE_ID
"""

import os
import sys
import json
import argparse
import requests
from datetime import datetime

# Render API Documentation:
# https://render.com/docs/api-reference

RENDER_API_BASE = "https://api.render.com/v1"

RENDER_DATABASE_URL = "postgresql://flaskwebpostgresql_user:nrDeXdaJQ2GA9Bv04ISC2rdNpI7EKhYr@dpg-d47l9824d50c7388ofsg-a.singapore-postgres.render.com/flaskwebpostgresql"

def get_render_token():
    """Lấy Render API token từ environment hoặc user input"""
    token = os.environ.get('RENDER_API_TOKEN')
    if token:
        print(f"[✓] Render API token từ environment variable")
        return token

    print("[!] RENDER_API_TOKEN environment variable không tìm thấy")
    print("\nCách lấy API token:")
    print("1. Vào https://dashboard.render.com/account/api-tokens")
    print("2. Tạo API token mới")
    print("3. Copy token")
    print("\nSau đó chạy lệnh:")
    print('  set RENDER_API_TOKEN=your_token_here')
    print('  python setup_render_database_url.py\n')

    token = input("Hoặc nhập Render API token ngay: ").strip()
    if not token:
        print("[✗] Token là bắt buộc")
        return None
    return token

def get_service_id(api_token):
    """Lấy service ID cho web service"""
    print("\n[*] Lấy danh sách services từ Render...")

    headers = {"Authorization": f"Bearer {api_token}"}
    try:
        response = requests.get(f"{RENDER_API_BASE}/services", headers=headers)
        response.raise_for_status()
        services = response.json()

        # Tìm service có tên chứa 'c-cash' hoặc 'bks'
        web_services = [s for s in services if s.get('type') == 'web_service']

        if not web_services:
            print("[✗] Không tìm thấy web service nào")
            return None

        print("\n[ℹ] Services tìm thấy:")
        for idx, svc in enumerate(web_services, 1):
            name = svc.get('name', 'Unknown')
            svc_id = svc.get('id', 'Unknown')
            print(f"  [{idx}] {name} (ID: {svc_id})")

        # Tự động chọn nếu chỉ có 1 service hoặc nếu tìm thấy 'c-cash-bks'
        if len(web_services) == 1:
            return web_services[0]['id']

        for svc in web_services:
            if 'c-cash' in svc.get('name', '').lower():
                return svc['id']

        # Nếu không tìm thấy tự động, hỏi user
        choice = input("\nChọn service (số hoặc ID): ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(web_services):
                return web_services[idx]['id']
        except ValueError:
            # Giả sử user nhập service ID trực tiếp
            return choice

        return None
    except Exception as e:
        print(f"[✗] Lỗi khi lấy services: {e}")
        return None

def update_environment_variable(api_token, service_id):
    """Update DATABASE_URL environment variable"""
    print(f"\n[*] Cập nhật DATABASE_URL cho service {service_id}...")

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    # Payload để update environment variables
    env_var_data = {
        "key": "DATABASE_URL",
        "value": RENDER_DATABASE_URL,
        "isFile": False,
    }

    try:
        # Lấy environment variables hiện tại
        response = requests.get(
            f"{RENDER_API_BASE}/services/{service_id}/env-vars",
            headers=headers
        )
        response.raise_for_status()
        current_vars = response.json()

        # Kiểm tra DATABASE_URL đã tồn tại hay chưa
        db_url_exists = any(v.get('key') == 'DATABASE_URL' for v in current_vars)

        if db_url_exists:
            print("[ℹ] DATABASE_URL đã tồn tại, sẽ cập nhật...")
        else:
            print("[ℹ] DATABASE_URL chưa tồn tại, sẽ thêm mới...")

        # Update/Create environment variable
        response = requests.post(
            f"{RENDER_API_BASE}/services/{service_id}/env-vars",
            headers=headers,
            json=env_var_data
        )

        if response.status_code == 409:
            # Variable đã tồn tại, cập nhật thay vì thêm
            print("[*] Variable đã tồn tại, cập nhật...")
            response = requests.patch(
                f"{RENDER_API_BASE}/services/{service_id}/env-vars/DATABASE_URL",
                headers=headers,
                json={"value": RENDER_DATABASE_URL}
            )

        response.raise_for_status()
        print("[✓] DATABASE_URL được cập nhật thành công!")
        return True

    except Exception as e:
        print(f"[✗] Lỗi khi cập nhật environment variable: {e}")
        return False

def trigger_redeploy(api_token, service_id):
    """Trigger redeploy"""
    print(f"\n[*] Trigger redeploy cho service {service_id}...")

    headers = {"Authorization": f"Bearer {api_token}"}

    try:
        response = requests.post(
            f"{RENDER_API_BASE}/services/{service_id}/deploys",
            headers=headers,
            json={}
        )
        response.raise_for_status()
        print("[✓] Redeploy triggered!")
        print("\n[ℹ] Bạn có thể kiểm tra status tại: https://dashboard.render.com")
        return True

    except Exception as e:
        print(f"[✗] Lỗi khi trigger redeploy: {e}")
        print("\n[!] Bạn có thể trigger redeploy thủ công:")
        print("1. Vào https://dashboard.render.com")
        print("2. Chọn web service")
        print("3. Click 'Manual Deploy' → 'Deploy latest commit'")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Setup DATABASE_URL trên Render.com"
    )
    parser.add_argument(
        '--token',
        help='Render API token (hoặc set RENDER_API_TOKEN env variable)'
    )
    parser.add_argument(
        '--service-id',
        help='Service ID của web service'
    )
    parser.add_argument(
        '--skip-redeploy',
        action='store_true',
        help='Không trigger redeploy sau khi update'
    )

    args = parser.parse_args()

    print("="*80)
    print("RENDER DATABASE_URL SETUP")
    print("="*80)

    # Lấy API token
    token = args.token or get_render_token()
    if not token:
        return

    # Lấy service ID
    service_id = args.service_id or get_service_id(token)
    if not service_id:
        return

    # Update environment variable
    if not update_environment_variable(token, service_id):
        return

    # Trigger redeploy
    if not args.skip_redeploy:
        trigger_redeploy(token, service_id)

    print("\n" + "="*80)
    print("✅ SETUP COMPLETE!")
    print("="*80)
    print("\nKiểm tra logs tại: https://dashboard.render.com")
    print("- Tìm message 'Database: OK' hoặc tương tự")
    print("- Không nên có lỗi 'Connection refused'")

if __name__ == '__main__':
    # Check if requests library is available
    try:
        import requests
    except ImportError:
        print("[✗] requests library không được cài đặt")
        print("Cài đặt: pip install requests")
        sys.exit(1)

    main()
