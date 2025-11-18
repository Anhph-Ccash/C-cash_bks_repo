#!/usr/bin/env python3
"""
Script kiểm tra scan_ranges data trong database
"""

from app import app
from models.bank_config import BankConfig
from extensions import db

with app.app_context():
    print("=== KIỂM TRA SCAN_RANGES DATA ===\n")

    # Lấy tất cả bank configs
    configs = BankConfig.query.all()

    print(f"Tổng số BankConfig: {len(configs)}\n")

    if len(configs) == 0:
        print("⚠️ Không có BankConfig nào trong database!")
    else:
        for cfg in configs:
            print(f"📌 Bank: {cfg.bank_code} - {cfg.bank_name or 'N/A'}")
            print(f"   Company ID: {cfg.company_id}")
            print(f"   Keywords: {cfg.keywords}")

            # Kiểm tra scan_ranges
            if cfg.scan_ranges:
                print(f"   ✅ Scan Ranges: {len(cfg.scan_ranges)} vùng")
                for i, range_data in enumerate(cfg.scan_ranges, 1):
                    print(f"      {i}. {range_data.get('name', 'N/A')} ({range_data.get('start_row', '?')}-{range_data.get('end_row', '?')})")
                    if range_data.get('description'):
                        print(f"         Mô tả: {range_data.get('description')}")
            else:
                print(f"   ⚠️ Scan Ranges: Chưa có (null hoặc empty)")

            print()

    # Kiểm tra column trong database
    print("\n=== KIỂM TRA COLUMN TRONG DB ===")
    try:
        result = db.session.execute(db.text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'bank_config' AND column_name = 'scan_ranges'
        """))

        row = result.fetchone()
        if row:
            print(f"✅ Column 'scan_ranges' tồn tại:")
            print(f"   Type: {row[1]}")
            print(f"   Nullable: {row[2]}")
        else:
            print("❌ Column 'scan_ranges' KHÔNG tồn tại trong bảng bank_config!")
    except Exception as e:
        print(f"❌ Lỗi khi kiểm tra column: {e}")

    # Test thêm sample data
    print("\n=== THÊM SAMPLE DATA (nếu cần) ===")
    sample_config = BankConfig.query.filter_by(bank_code='TEST_SCAN').first()

    if not sample_config:
        print("Tạo BankConfig mẫu...")
        try:
            sample = BankConfig(
                company_id=1,
                bank_code='TEST_SCAN',
                bank_name='Test Scan Ranges',
                keywords=['test', 'sample'],
                scan_ranges=[
                    {
                        "name": "Header",
                        "description": "Phần header test",
                        "start_row": 1,
                        "end_row": 10
                    },
                    {
                        "name": "Data",
                        "description": "Phần dữ liệu test",
                        "start_row": 15,
                        "end_row": 100
                    }
                ],
                is_active=True
            )
            db.session.add(sample)
            db.session.commit()
            print("✅ Đã tạo sample BankConfig với scan_ranges!")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Lỗi khi tạo sample: {e}")
    else:
        print(f"Sample config đã tồn tại: {sample_config.bank_code}")
        if sample_config.scan_ranges:
            print(f"   Có {len(sample_config.scan_ranges)} scan ranges")
        else:
            print("   ⚠️ Chưa có scan_ranges, đang cập nhật...")
            try:
                sample_config.scan_ranges = [
                    {
                        "name": "Header Updated",
                        "start_row": 1,
                        "end_row": 10
                    },
                    {
                        "name": "Data Updated",
                        "start_row": 15,
                        "end_row": 100
                    }
                ]
                db.session.commit()
                print("   ✅ Đã cập nhật scan_ranges!")
            except Exception as e:
                db.session.rollback()
                print(f"   ❌ Lỗi cập nhật: {e}")
