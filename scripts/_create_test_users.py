"""
在生產環境建立獨立的平台 superuser 帳號（tenant_id=NULL），
並將 y.c.chen1112@gmail.com 的 is_superuser 改為 False（純租戶 Owner）。

執行方式:
  docker cp scripts/_create_test_users.py aihr-web-1:/code/fix_superuser.py
  docker exec -w /code aihr-web-1 python3 fix_superuser.py
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
    # 找一個任意 tenant_id 用來滿足 FK（migration 跑完後才能 NULL）
    # 先用 Demo Tenant，migration 後再清空
    from app.models.tenant import Tenant
    any_tenant = db.query(Tenant).first()
    u = User(
        id=uuid.uuid4(),
        email=PLATFORM_EMAIL,
        full_name="平台管理員",
        hashed_password=get_password_hash(PLATFORM_PASSWORD),
        role="owner",
        tenant_id=any_tenant.id,  # 暫時，migration 後改 NULL
        is_superuser=True,
        email_verified=True,
        agreed_to_terms=True,
        status="active",
    )
    db.add(u)
    db.commit()
    print(f"CREATED: {PLATFORM_EMAIL} (is_superuser=True, 暫時掛 tenant)")

# ── 2. 移除舊帳號的 is_superuser ──
owner = db.query(User).filter(User.email == TENANT_OWNER_EMAIL).first()
if owner:
    if owner.is_superuser:
        owner.is_superuser = False
        db.commit()
        print(f"UPDATED: {TENANT_OWNER_EMAIL} → is_superuser=False (純租戶 Owner)")
    else:
        print(f"SKIP: {TENANT_OWNER_EMAIL} 已是 is_superuser=False")
else:
    print(f"NOT FOUND: {TENANT_OWNER_EMAIL}")

db.close()
print("Done.")
