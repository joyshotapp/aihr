"""
重整帳號結構：
1. 建立 owner@upower.demo (role=owner, tenant=Demo Tenant, UniHR@2026)
2. y.c.chen1112@gmail.com → is_superuser=True, tenant_id=NULL, 更新密碼
3. 停用 platform@unihr.internal（已無用）
"""
import sys
sys.path.insert(0, '/code')

from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash
import uuid

db = SessionLocal()

TENANT_ID = "b3202138-1a11-4322-bdf7-666d4a07f1fc"

# ── 1. 建立 owner@upower.demo ──
existing = db.query(User).filter(User.email == "owner@upower.demo").first()
if existing:
    print("SKIP (exists): owner@upower.demo")
else:
    u = User(
        id=uuid.uuid4(),
        email="owner@upower.demo",
        full_name="公司擁有者",
        hashed_password=get_password_hash("UniHR@2026"),
        role="owner",
        tenant_id=TENANT_ID,
        is_superuser=False,
        email_verified=True,
        agreed_to_terms=True,
        status="active",
    )
    db.add(u)
    db.commit()
    print("CREATED: owner@upower.demo (role=owner, UniHR@2026)")

# ── 2. y.c.chen1112@gmail.com → 系統方 superuser ──
me = db.query(User).filter(User.email == "y.c.chen1112@gmail.com").first()
if me:
    me.is_superuser = True
    me.tenant_id = None
    me.hashed_password = get_password_hash("Bravomix0715")
    db.commit()
    print("UPDATED: y.c.chen1112@gmail.com → is_superuser=True, tenant_id=NULL, 密碼已更新")
else:
    print("NOT FOUND: y.c.chen1112@gmail.com")

# ── 3. 停用 platform@unihr.internal ──
platform = db.query(User).filter(User.email == "platform@unihr.internal").first()
if platform:
    platform.status = "inactive"
    db.commit()
    print("DEACTIVATED: platform@unihr.internal")

# ── 4. 最終狀態 ──
print("\n--- 最終帳號狀態 ---")
for u in db.query(User).order_by(User.created_at).all():
    tid = "NULL" if u.tenant_id is None else str(u.tenant_id)[:8] + "..."
    print(f"  {u.email:<42} role={u.role:<12} su={u.is_superuser} status={u.status} tenant={tid}")

db.close()
print("\nDone.")
