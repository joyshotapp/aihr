#!/usr/bin/env python3
"""
Demo data seeder for UniHR admin panel.

Usage:
    # Seed demo data (idempotent — safe to run multiple times)
    python scripts/seed_demo_data.py

    # Remove all demo data
    python scripts/seed_demo_data.py --clean
"""

from __future__ import annotations

import argparse
import os
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("POSTGRES_SERVER", "localhost:5436")
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("REDIS_PORT", "6381")
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("ADMIN_IP_WHITELIST_ENABLED", "false")

import sqlalchemy as sa
from sqlalchemy import text

# ── DB connection ─────────────────────────────────────────────────────────────

def get_engine():
    from app.db.session import engine
    return engine


# ── Seed constants ────────────────────────────────────────────────────────────

DEMO_MARKER = "demo-seed"  # stored in data_residency_note to identify demo rows

TENANTS = [
    {"name": "台積電人資部門", "plan": "enterprise", "status": "active",
     "max_users": 200, "max_documents": 5000, "max_storage_mb": 20480,
     "monthly_query_limit": 50000, "monthly_token_limit": 10_000_000,
     "quota_alert_threshold": 0.8, "region": "tw"},
    {"name": "鴻海精密科技", "plan": "pro", "status": "active",
     "max_users": 50, "max_documents": 1000, "max_storage_mb": 5120,
     "monthly_query_limit": 10000, "monthly_token_limit": 2_000_000,
     "quota_alert_threshold": 0.8, "region": "tw"},
    {"name": "永豐金控", "plan": "pro", "status": "active",
     "max_users": 50, "max_documents": 1000, "max_storage_mb": 5120,
     "monthly_query_limit": 10000, "monthly_token_limit": 2_000_000,
     "quota_alert_threshold": 0.8, "region": "tw"},
    {"name": "聯發科技", "plan": "pro", "status": "active",
     "max_users": 50, "max_documents": 1000, "max_storage_mb": 5120,
     "monthly_query_limit": 10000, "monthly_token_limit": 2_000_000,
     "quota_alert_threshold": 0.85, "region": "tw"},
    {"name": "統一超商 HR", "plan": "free", "status": "active",
     "max_users": 5, "max_documents": 50, "max_storage_mb": 512,
     "monthly_query_limit": 500, "monthly_token_limit": 100_000,
     "quota_alert_threshold": 0.9, "region": "tw"},
    {"name": "遠東新世紀", "plan": "free", "status": "trial",
     "max_users": 5, "max_documents": 50, "max_storage_mb": 512,
     "monthly_query_limit": 500, "monthly_token_limit": 100_000,
     "quota_alert_threshold": 0.9, "region": "tw"},
    {"name": "富邦媒體科技", "plan": "pro", "status": "suspended",
     "max_users": 50, "max_documents": 1000, "max_storage_mb": 5120,
     "monthly_query_limit": 10000, "monthly_token_limit": 2_000_000,
     "quota_alert_threshold": 0.8, "region": "tw"},
]

PLAN_PRICE_TWD = {"free": 0, "pro": 2980, "enterprise": 12800}

ACTION_TYPES = ["qa_query", "document_parse", "embedding", "qa_query", "qa_query"]


def rnd(seed: int) -> random.Random:
    return random.Random(seed)


# ── Core seeder ───────────────────────────────────────────────────────────────

def seed(conn: sa.Connection) -> None:
    now = datetime.now(timezone.utc)

    # ── 1. Tenants ────────────────────────────────────────────────────────────
    print("Seeding tenants...")
    tenant_ids: list[uuid.UUID] = []
    for i, t in enumerate(TENANTS):
        tid = uuid.uuid5(uuid.NAMESPACE_DNS, f"demo-tenant-{i}")
        existing = conn.execute(
            text("SELECT id FROM tenants WHERE id = :id"), {"id": str(tid)}
        ).fetchone()
        if not existing:
            conn.execute(text("""
                INSERT INTO tenants (
                    id, name, plan, status,
                    max_users, max_documents, max_storage_mb,
                    monthly_query_limit, monthly_token_limit, quota_alert_threshold,
                    region, data_residency_note, created_at, updated_at
                ) VALUES (
                    :id, :name, :plan, :status,
                    :max_users, :max_documents, :max_storage_mb,
                    :monthly_query_limit, :monthly_token_limit, :quota_alert_threshold,
                    :region, :note, :created_at, :updated_at
                )
            """), {
                "id": str(tid), **t,
                "note": DEMO_MARKER,
                "created_at": now - timedelta(days=60 - i * 7),
                "updated_at": now - timedelta(days=i),
            })
        tenant_ids.append(tid)

    # ── 2. Users (one owner per tenant) ──────────────────────────────────────
    print("Seeding users...")
    DEMO_PASSWORD_HASH = "$2b$12$demoplaceholderhashedpasswordXXXXXXXXXXXXXXXXXXXXXXX"
    user_ids: dict[uuid.UUID, list[uuid.UUID]] = {}
    names = [
        ("王小明", "owner"), ("李美玲", "owner"), ("陳志豪", "owner"),
        ("林雅婷", "owner"), ("黃建國", "owner"), ("吳佳蓉", "owner"),
        ("張偉民", "owner"),
    ]
    for i, tid in enumerate(tenant_ids):
        full_name, role = names[i]
        domain = TENANTS[i]["name"].replace(" ", "").lower()[:8]
        uid = uuid.uuid5(uuid.NAMESPACE_DNS, f"demo-user-owner-{i}")
        existing = conn.execute(
            text("SELECT id FROM users WHERE id = :id"), {"id": str(uid)}
        ).fetchone()
        if not existing:
            conn.execute(text("""
                INSERT INTO users (
                    id, email, full_name, hashed_password, status, role,
                    is_superuser, mfa_enabled, email_verified, agreed_to_terms,
                    tenant_id, created_at, updated_at
                ) VALUES (
                    :id, :email, :full_name, :pw, 'active', :role,
                    false, false, true, true,
                    :tenant_id, :created_at, :updated_at
                )
            """), {
                "id": str(uid), "email": f"owner{i+1}@{domain}.com",
                "full_name": full_name, "pw": DEMO_PASSWORD_HASH,
                "role": role, "tenant_id": str(tid),
                "created_at": now - timedelta(days=58 - i * 7),
                "updated_at": now,
            })
        user_ids[tid] = [uid]

    # ── 3. Usage records (90 days, realistic pattern) ─────────────────────────
    print("Seeding usage records (this may take a moment)...")
    # check if already seeded
    existing_count = conn.execute(
        text("SELECT COUNT(*) FROM usagerecords WHERE tenant_id = :tid"),
        {"tid": str(tenant_ids[0])}
    ).scalar()
    if existing_count and existing_count > 50:
        print("  Usage records already seeded, skipping.")
    else:
        # Map tenant to realistic daily query volume
        daily_base = [380, 120, 95, 210, 8, 3, 0]
        for t_idx, tid in enumerate(tenant_ids):
            r = rnd(t_idx * 100)
            base = daily_base[t_idx]
            uids = user_ids[tid]
            for day_offset in range(90):
                date = now - timedelta(days=90 - day_offset)
                # Weekend dip
                weekday = date.weekday()
                multiplier = 0.2 if weekday >= 5 else 1.0
                # Growth trend: 30% more in recent 30 days
                growth = 1.3 if day_offset > 60 else 1.0
                n_queries = max(0, int(r.gauss(base * multiplier * growth, base * 0.2 * multiplier)))

                for _ in range(n_queries):
                    action = r.choice(ACTION_TYPES)
                    input_tok = r.randint(200, 800)
                    output_tok = r.randint(100, 500)
                    emb = 1 if action in ("embedding", "document_parse") else 0
                    pine = 1 if action == "qa_query" else 0
                    cost = (input_tok * 0.000003 + output_tok * 0.000015
                            + emb * 0.0001 + pine * 0.00004)
                    rec_id = uuid.uuid4()
                    conn.execute(text("""
                        INSERT INTO usagerecords (
                            id, tenant_id, user_id, action_type,
                            input_tokens, output_tokens, pinecone_queries,
                            embedding_calls, latency_ms, estimated_cost_usd, created_at
                        ) VALUES (
                            :id, :tid, :uid, :action,
                            :inp, :out, :pine, :emb, :lat, :cost, :ts
                        )
                    """), {
                        "id": str(rec_id), "tid": str(tid),
                        "uid": str(r.choice(uids)),
                        "action": action, "inp": input_tok, "out": output_tok,
                        "pine": pine, "emb": emb,
                        "lat": r.randint(300, 3000), "cost": round(cost, 8),
                        "ts": date.replace(
                            hour=r.randint(8, 20),
                            minute=r.randint(0, 59),
                            second=r.randint(0, 59),
                        ),
                    })

    # ── 4. Billing records ────────────────────────────────────────────────────
    print("Seeding billing records...")
    for i, tid in enumerate(tenant_ids):
        plan = TENANTS[i]["plan"]
        price = PLAN_PRICE_TWD[plan]
        if price == 0:
            continue
        for month_offset in range(3):
            period_start = (now.replace(day=1) - timedelta(days=month_offset * 30)).replace(
                hour=0, minute=0, second=0, microsecond=0)
            period_end = (period_start + timedelta(days=31)).replace(day=1)
            inv_num = f"INV-{period_start.strftime('%Y%m')}-{str(tid)[:6].upper()}"
            existing = conn.execute(
                text("SELECT id FROM billing_records WHERE invoice_number = :inv"),
                {"inv": inv_num}
            ).fetchone()
            if not existing:
                conn.execute(text("""
                    INSERT INTO billing_records (
                        id, tenant_id, amount_twd, currency, status,
                        description, plan, period_start, period_end,
                        invoice_number, created_at
                    ) VALUES (
                        :id, :tid, :amount, 'TWD', :status,
                        :desc, :plan, :ps, :pe, :inv, :ts
                    )
                """), {
                    "id": str(uuid.uuid4()), "tid": str(tid),
                    "amount": price,
                    "status": "paid" if month_offset > 0 else "paid",
                    "desc": f"{TENANTS[i]['name']} — {plan.capitalize()} 方案月費",
                    "plan": plan,
                    "ps": period_start.replace(tzinfo=None),
                    "pe": period_end.replace(tzinfo=None),
                    "inv": inv_num,
                    "ts": period_start + timedelta(days=1),
                })

    # ── 5. Quota alerts ───────────────────────────────────────────────────────
    print("Seeding quota alerts...")
    alert_scenarios = [
        (0, "warning", "monthly_queries", 42000, 50000, 0.84),
        (1, "critical", "monthly_tokens", 1950000, 2000000, 0.975),
        (4, "warning", "monthly_queries", 430, 500, 0.86),
    ]
    for t_idx, alert_type, resource, cur, lim, ratio in alert_scenarios:
        tid = tenant_ids[t_idx]
        aid = uuid.uuid5(uuid.NAMESPACE_DNS, f"demo-alert-{t_idx}-{resource}")
        existing = conn.execute(
            text("SELECT id FROM quotaalerts WHERE id = :id"), {"id": str(aid)}
        ).fetchone()
        if not existing:
            conn.execute(text("""
                INSERT INTO quotaalerts (
                    id, tenant_id, alert_type, resource,
                    current_value, limit_value, usage_ratio,
                    message, notified, created_at
                ) VALUES (
                    :id, :tid, :atype, :resource,
                    :cur, :lim, :ratio,
                    :msg, false, :ts
                )
            """), {
                "id": str(aid), "tid": str(tid),
                "atype": alert_type, "resource": resource,
                "cur": cur, "lim": lim, "ratio": ratio,
                "msg": f"{TENANTS[t_idx]['name']} {resource} 使用率達 {ratio*100:.0f}%",
                "ts": now - timedelta(hours=3),
            })

    print("\n✅ Demo data seeded successfully.")
    print(f"   Tenants   : {len(TENANTS)}")
    print(f"   Users     : {len(TENANTS)} (1 owner per tenant)")
    print("   Usage     : ~90 days of realistic query history")
    print("   Billing   : 3 months of invoices for paid plans")
    print("   Alerts    : 3 quota alert scenarios")


def clean(conn: sa.Connection) -> None:
    print("Removing demo data...")
    # Find demo tenant IDs
    rows = conn.execute(
        text("SELECT id FROM tenants WHERE data_residency_note = :m"),
        {"m": DEMO_MARKER}
    ).fetchall()
    if not rows:
        print("No demo data found.")
        return
    tid_list = [str(r[0]) for r in rows]
    tid_sql = ",".join(f"'{t}'" for t in tid_list)

    conn.execute(text(f"DELETE FROM quotaalerts WHERE tenant_id IN ({tid_sql})"))
    conn.execute(text(f"DELETE FROM billing_records WHERE tenant_id IN ({tid_sql})"))
    conn.execute(text(f"DELETE FROM usagerecords WHERE tenant_id IN ({tid_sql})"))
    conn.execute(text(f"DELETE FROM users WHERE tenant_id IN ({tid_sql})"))
    conn.execute(text(f"DELETE FROM tenants WHERE id IN ({tid_sql})"))
    print(f"✅ Removed demo data for {len(tid_list)} tenants.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed or clean UniHR demo data.")
    parser.add_argument("--clean", action="store_true", help="Remove all demo data instead of seeding.")
    args = parser.parse_args()

    engine = get_engine()
    with engine.begin() as conn:
        if args.clean:
            clean(conn)
        else:
            seed(conn)


if __name__ == "__main__":
    main()
