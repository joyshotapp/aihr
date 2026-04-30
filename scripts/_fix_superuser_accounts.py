"""
修復 superuser 帳號分離：
1. 建立新平台 superuser（tenant_id=NULL）
2. 將 y.c.chen1112@gmail.com 的 is_superuser 改為 False

執行方式（在 aihr-web-1 容器內）:
  python3 /tmp/fix_superuser_accounts.py
"""
import sys
sys.path.insert(0, '/code')

from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash
import uuid

db = SessionLocal()

PLATFORM_EMAIL = "platform@unihr.internal"
PLATFORM_PASSWORD = "UniHR-Platform@2026!"
TENANT_OWNER_EMAIL = "y.c.chen1112@gmail.com"

# ── 1. 建立平台 superuser（tenant_id=NULL）──
existing = db.query(User).filter(User.email == PLATFORM_EMAIL).first()
if existing:
    print(f"SKIP (exists): {PLATFORM_EMAIL}")
else:
    u = User(
        id=uuid.uuid4(),
        email=PLATFORM_EMAIL,
        full_name="平台管理員",
        hashed_password=get_password_hash(PLATFORM_PASSWORD),
        role="owner",
        tenant_id=None,   # 獨立平台帳號，不屬於任何租戶
        is_superuser=True,
        email_verified=True,
        agreed_to_terms=True,
        status="active",
    )
    db.add(u)
    db.commit()
    print(f"CREATED: {PLATFORM_EMAIL} (is_superuser=True, tenant_id=NULL)")

# ── 2. 移除舊帳號的 is_superuser ──
owner = db.query(User).filter(User.email == TENANT_OWNER_EMAIL).first()
if owner:
    if owner.is_superuser:
        owner.is_superuser = False
        db.commit()
        print(f"UPDATED: {TENANT_OWNER_EMAIL} -> is_superuser=False (純租戶 Owner)")
    else:
        print(f"SKIP: {TENANT_OWNER_EMAIL} 已是 is_superuser=False")
else:
    print(f"NOT FOUND: {TENANT_OWNER_EMAIL}")

# ── 3. 確認最終狀態 ──
print("\n--- 最終帳號狀態 ---")
users = db.query(User).order_by(User.created_at).all()
for u in users:
    print(f"  {u.email:<40} role={u.role:<12} superuser={u.is_superuser} tenant={'NULL' if u.tenant_id is None else str(u.tenant_id)[:8]+'...'}")

db.close()
print("\nDone.")
