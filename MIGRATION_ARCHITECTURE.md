# Migration Architecture & Flow

## 📊 System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Migration System Architecture                             │
└─────────────────────────────────────────────────────────────────────────────┘

                          LOCAL ENVIRONMENT
                          ════════════════════
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
          ┌──────────────────┐          ┌──────────────────┐
          │  PostgreSQL      │          │  Python Scripts  │
          │  Local DB        │          │  (Windows)       │
          │  11 Users        │          │                  │
          │  ├─ admin        │          │ • migrate_*.py   │
          │  ├─ user21       │          │ • restore_*.py   │
          │  ├─ user3        │          │ • check_db.py    │
          │  └─ ...          │          │ • manage_*.py    │
          └──────────────────┘          └──────────────────┘
                    │                               │
                    │                               │
                    └───────────────┬───────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │  Migration Flow               │
                    │  1. Read Users                │
                    │  2. Create Backup             │
                    │  3. Transform Data            │
                    │  4. Upload to Render          │
                    └───────────────┬───────────────┘
                                    │
                                    ▼
                      ┌──────────────────────────┐
                      │   RENDER.COM CLOUD       │
                      │   ════════════════════   │
                      │                          │
                      │   PostgreSQL DB          │
                      │   ├─ users (empty)       │
                      │   ├─ Insert 11 users     │
                      │   └─ Verify              │
                      │                          │
                      │   Used by:               │
                      │   - Flask App            │
                      │   - Admin Panel          │
                      │   - User Auth            │
                      └──────────────────────────┘
```

---

## 🔄 Migration Process Flow

```
START
  │
  ├──► [1] Connect Databases ◄─────────────────────┐
  │      • Local DB: OK                              │
  │      • Render DB: OK                             │
  │      └─► SUCCESS                                 │
  │         │                                        │
  ├──► [2] Read Users from Local ◄────────────────┐ │
  │      • SELECT * FROM users                      │ │
  │      • Got 11 users                             │ │
  │      └─► SUCCESS                                │ │
  │         │                                        │ │
  ├──► [3] CHOICE ◄────────────────────────────────┼─┤
  │      ├─ Preview?  → Show Users & Exit           │ │
  │      ├─ Backup?   → Save JSON File & Exit       │ │
  │      ├─ Execute?  → Continue ▼                  │ │
  │      └─ Exit?     → Done                        │ │
  │         │                                        │ │
  │         ▼                                        │ │
  ├──► [4] User Confirmation ◄────────────────────┬┘ │
  │      • Display: "Migrate 11 users?"               │
  │      • Input: yes/no                             │
  │      ├─ if NO  → Abort & Exit                   │
  │      └─ if YES → Continue ▼                     │
  │         │                                        │
  ├──► [5] Create Backup ◄──────────────────────────┤
  │      • Read all users again                      │
  │      • Save to: backups/users_backup_*.json     │
  │      • File created & dated                      │
  │      └─► SUCCESS                                 │
  │         │                                        │
  ├──► [6] Delete Old Data on Render ◄──────────────┤
  │      • DELETE FROM user_companies               │
  │      • DELETE FROM users                        │
  │      • X users deleted (cleanup)                 │
  │      └─► SUCCESS                                 │
  │         │                                        │
  ├──► [7] Insert Users to Render ◄─────────────────┤
  │      • Loop through 11 users                     │
  │      • INSERT INTO users (...)                   │
  │      • Each user inserted                        │
  │      • 11 rows affected                          │
  │      └─► SUCCESS                                 │
  │         │                                        │
  ├──► [8] Verify Migration ◄───────────────────────┤
  │      • SELECT COUNT(*) FROM users on Render     │
  │      • Compare: 11 == 11 ✓                      │
  │      └─► SUCCESS                                 │
  │         │                                        │
  └──► END: Migration Complete! ✓
```

---

## 📝 Database Schema Migration

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        TABLE: users                                      │
├──────────────────────────────────────────────────────────────────────────┤
│ Column         │ Type       │ Constraints          │ Migration Status   │
├────────────────┼────────────┼──────────────────────┼────────────────────┤
│ id             │ INTEGER    │ PRIMARY KEY          │ ✓ Migrated         │
│ username       │ VARCHAR    │ NOT NULL, UNIQUE     │ ✓ Migrated         │
│ email          │ VARCHAR    │ NOT NULL             │ ✓ Migrated         │
│ password_hash  │ VARCHAR    │ NOT NULL             │ ✓ Migrated         │
│ role           │ VARCHAR    │ Nullable (default)   │ ✓ Migrated         │
│ fullname       │ VARCHAR    │ Nullable             │ ✓ Migrated         │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│                    TABLE: user_companies (Related)                       │
├──────────────────────────────────────────────────────────────────────────┤
│ Status: Not required for users table migration                           │
│ Action: Preserved if exists, foreign keys handled safely                │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 🔐 Data Integrity & Safety

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      Safety Measures                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│ 1. PRE-MIGRATION CHECKS                                                │
│    ├─ Connection test (both databases)                                 │
│    ├─ User count verification                                          │
│    └─ Data preview before execution                                    │
│                                                                          │
│ 2. BACKUP CREATION                                                      │
│    ├─ JSON file with all user data                                     │
│    ├─ Timestamped filename                                             │
│    ├─ Stored in backups/ folder                                        │
│    └─ Can be restored anytime                                          │
│                                                                          │
│ 3. TRANSACTION MANAGEMENT                                               │
│    ├─ DELETE old data inside transaction                               │
│    ├─ INSERT new data inside transaction                               │
│    ├─ ROLLBACK on error                                                │
│    └─ Commit only on success                                           │
│                                                                          │
│ 4. VERIFICATION STEPS                                                    │
│    ├─ Count check (local vs render)                                    │
│    ├─ Data integrity validation                                        │
│    └─ User details spot check                                          │
│                                                                          │
│ 5. RECOVERY OPTIONS                                                      │
│    ├─ Backup files for restore                                         │
│    ├─ Restore script available                                         │
│    └─ Can re-run migration anytime                                     │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Data Movement Timeline

```
Timeline of Data Movement:

LOCAL DB                     ACTION                    RENDER DB
════════════════════════════════════════════════════════════════════════

11 Users Present
    │
    ├──► [1] READ (SELECT)
    │    └─► 11 Users Loaded
    │
    ├──► [2] BACKUP (JSON)
    │    └─► backups/users_backup_20241124_143022.json
    │
    ├──► [3] TRANSFER
    │         ├─► Over HTTPS Connection
    │         ├─► Connection Pool (Secure)
    │         └─► PostgreSQL Network Protocol
    │
    │                                    [1] DELETE Old (0 Users)
    │                                        └─► No old data
    │
    │                                    [2] INSERT 11 Users
    │                                        ├─ user 3: admin
    │                                        ├─ user 5: user21
    │                                        ├─ user 6: user3
    │                                        ├─ ...
    │                                        └─ user 14: anh.pham
    │
    │                                    [3] VERIFY
    │                                        └─ 11 Users Present ✓
    │
    └──► COMPLETE
         Backup saved
         11 Users migrated
         Both DBs in sync

```

---

## 🔄 Workflow Options

```
Option 1: PREVIEW ONLY
═══════════════════════════════════════════════════════════════════
  python migrate_users_to_render.py --preview
         │
         ├─ Read users from local
         ├─ Display users info
         └─ EXIT (no changes)

Result: See what would be migrated, nothing changes

───────────────────────────────────────────────────────────────────

Option 2: PREVIEW + BACKUP
═══════════════════════════════════════════════════════════════════
  python migrate_users_to_render.py --preview --backup
         │
         ├─ Read users
         ├─ Display preview
         ├─ Create backup file
         └─ EXIT

Result: See what would be migrated + backup saved, nothing changes

───────────────────────────────────────────────────────────────────

Option 3: FULL MIGRATION (RECOMMENDED)
═══════════════════════════════════════════════════════════════════
  python migrate_users_to_render.py --execute
         │
         ├─ Read users
         ├─ Ask for confirmation (yes/no)
         ├─ Create backup
         ├─ Delete old data on Render
         ├─ Insert new users
         ├─ Verify data
         └─ COMPLETE

Result: Users migrated to Render, backup saved

───────────────────────────────────────────────────────────────────

Option 4: RESTORE FROM BACKUP
═══════════════════════════════════════════════════════════════════
  python restore_users_from_backup.py backups/users_backup_*.json --execute
         │
         ├─ Load backup file
         ├─ Ask for confirmation (yes/no)
         ├─ Delete current users on Render
         ├─ Insert users from backup
         └─ COMPLETE

Result: Users restored from backup (for recovery)
```

---

## 🎯 Success Criteria Checklist

```
BEFORE MIGRATION
════════════════════════════════════════════════════════════════════
□ PostgreSQL Local Database running
□ Can connect to Local DB (11 users visible)
□ Render Database URL obtained from Render Dashboard
□ Can connect to Render DB (empty or existing)
□ Python 3.7+ with SQLAlchemy installed
□ Migration scripts downloaded to C-cash_bks_repo/

DURING MIGRATION
════════════════════════════════════════════════════════════════════
□ Run preview: see 11 users listed
□ Run backup: get backup file in backups/ folder
□ Run execute: confirm yes when prompted
□ Migration completes without errors
□ Log shows all steps successful

AFTER MIGRATION
════════════════════════════════════════════════════════════════════
□ Check render DB: 11 users present
□ Verify each user: username, email, role correct
□ Password hashes intact (not changed)
□ Backup file saved and accessible
□ Application can connect to Render DB
□ Users can login with existing passwords

OPTIONAL VERIFICATION
════════════════════════════════════════════════════════════════════
□ Run application with Render DB connection string
□ Test user login
□ Check user permissions and roles
□ Verify no data loss
```

---

## 📈 Performance & Timing

```
Typical Migration Times (11 Users)
════════════════════════════════════════════════════════════════════

Operation              Estimated Time    Network
───────────────────────────────────────────────────────────────────
Connect Databases           2-3 sec       DNS + TCP handshake
Read Users (Local)          1-2 sec       Local query
Create Backup               <1 sec        File I/O
Transfer Data               3-5 sec       HTTPS to Render
Insert on Render            2-3 sec       Remote INSERT
Verify Data                 1-2 sec       COUNT query
───────────────────────────────────────────────────────────────────
TOTAL                      10-15 sec      All operations

Factors affecting timing:
• Network latency (local to Render)
• Database server load
• Number of users
• Data payload size
```

---

## 🔍 Monitoring During Migration

```
Terminal Output Example
════════════════════════════════════════════════════════════════════

[*] Kết nối đến Local Database...
[✓] Local Database: OK

[*] Kết nối đến Render Database...
[✓] Render Database: OK

[✓] Lấy được 11 users từ Local Database

[*] Bắt đầu migration...
[✓] Backup thành công: backups/users_backup_20241124_143022.json
[✓] Xóa 0 users cũ trên Render Database
[✓] Migrate thành công 11 users lên Render Database
[✓] Xác minh thành công: 11 users trên Render Database

[✓] Migration hoàn thành!
```

---

**Migration System Diagram** - See above for complete visual overview of the migration architecture and data flow.
