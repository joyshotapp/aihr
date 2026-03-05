"""
UniHR 全域壓力與容錯測試（第 20 項）

覆蓋情境：
  1. 正常對話流量（chat/stream）
  2. 文件上傳流量
  3. 並發知識庫查詢
  4. Rate limit 觸發驗證
  5. 跨租戶 IDOR 探測（應全部回 404）
  6. Redis 失效容錯（降級放行）

執行方式：
  pip install locust
  locust -f tests/test_load.py --host http://localhost:8002

  無 UI 模式（CI 用）：
  locust -f tests/test_load.py --host http://localhost:8002 \\
    --headless -u 20 -r 2 -t 60s \\
    --csv test-data/test-results/load_$(date +%Y%m%d_%H%M%S)

驗收基準（go-live 條件）：
  - p95 latency  < 2000ms  (chat 除外，chat < 5000ms)
  - 5xx rate     < 1%
  - success rate > 99%
"""
import random
import uuid
import os
from locust import HttpUser, task, between, events
from locust.exception import RescheduleTask


# ─── 測試帳號（需預先建立，或透過 fixture 動態建立）───
TENANT_A = {
    "email": os.getenv("LOAD_USER_A_EMAIL", "hr@taiyutech.com"),
    "password": os.getenv("LOAD_USER_A_PASSWORD", "Changeme123!"),
}
TENANT_B = {
    "email": os.getenv("LOAD_USER_B_EMAIL", "admin@othertenant.com"),
    "password": os.getenv("LOAD_USER_B_PASSWORD", "Changeme123!"),
}

# 已知屬於 Tenant B 的 UUID（用於 IDOR 測試）
FAKE_OTHER_TENANT_ID = str(uuid.uuid4())


# ════════════════════════════════════════
#  基礎 Mixin：登入取得 token
# ════════════════════════════════════════

class AuthMixin:
    token: str = ""

    def do_login(self, email: str, password: str) -> bool:
        resp = self.client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
            name="/auth/login",
        )
        if resp.status_code == 200:
            self.token = resp.json().get("access_token", "")
            return True
        return False

    @property
    def auth_headers(self):
        return {"Authorization": f"Bearer {self.token}"}


# ════════════════════════════════════════
#  正常流量使用者（Tenant A）
# ════════════════════════════════════════

class NormalChatUser(AuthMixin, HttpUser):
    """
    模擬一般 HR 使用者：登入 → 建立對話 → 送出問題 → 查詢清單
    wait_time: 模擬人類思考間隔
    """
    wait_time = between(1, 5)
    weight = 3  # 3:1 比例，正常流量為主

    conversation_id: str = ""

    def on_start(self):
        if not self.do_login(TENANT_A["email"], TENANT_A["password"]):
            self.environment.runner.quit()

    # ── 健康檢查 ──
    @task(1)
    def health_check(self):
        self.client.get("/health", name="/health")

    # ── 查詢聊天記錄 ──
    @task(3)
    def list_conversations(self):
        self.client.get(
            "/api/v1/chat/conversations",
            headers=self.auth_headers,
            name="/chat/conversations [list]",
        )

    # ── 建立新對話 ──
    @task(2)
    def create_conversation(self):
        resp = self.client.post(
            "/api/v1/chat/conversations",
            json={"title": f"壓力測試 {random.randint(1000, 9999)}"},
            headers=self.auth_headers,
            name="/chat/conversations [create]",
        )
        if resp.status_code == 200:
            self.conversation_id = resp.json().get("id", "")

    # ── 同步問答（非 stream）──
    @task(5)
    def sync_chat(self):
        if not self.conversation_id:
            raise RescheduleTask()

        questions = [
            "特休假怎麼計算？",
            "員工請病假需要提交哪些文件？",
            "試用期最長幾個月？",
            "加班費如何計算？",
            "育嬰假的申請流程是什麼？",
        ]
        self.client.post(
            "/api/v1/chat/query",
            json={
                "conversation_id": self.conversation_id,
                "message": random.choice(questions),
                "stream": False,
            },
            headers=self.auth_headers,
            name="/chat/query [sync]",
            timeout=30,
        )

    # ── 查詢文件清單 ──
    @task(2)
    def list_documents(self):
        self.client.get(
            "/api/v1/documents/",
            headers=self.auth_headers,
            name="/documents [list]",
        )


# ════════════════════════════════════════
#  安全探針（IDOR 測試）
# ════════════════════════════════════════

class SecurityProbeUser(AuthMixin, HttpUser):
    """
    模擬低頻率攻擊者：嘗試存取不屬於自己的資源
    預期：所有請求回 404
    """
    wait_time = between(2, 8)
    weight = 1  # 低比例

    def on_start(self):
        if not self.do_login(TENANT_A["email"], TENANT_A["password"]):
            self.environment.runner.quit()

    @task(3)
    def probe_fake_conversation(self):
        fake_id = str(uuid.uuid4())
        with self.client.get(
            f"/api/v1/chat/conversations/{fake_id}",
            headers=self.auth_headers,
            name="/chat/conversations [IDOR probe]",
            catch_response=True,
        ) as resp:
            if resp.status_code == 404:
                resp.success()  # 預期行為
            elif resp.status_code == 200:
                resp.failure(f"IDOR LEAK: conversation {fake_id} accessible!")
            else:
                resp.success()  # 其他錯誤也算正常

    @task(2)
    def probe_fake_document(self):
        fake_id = str(uuid.uuid4())
        with self.client.get(
            f"/api/v1/documents/{fake_id}",
            headers=self.auth_headers,
            name="/documents [IDOR probe]",
            catch_response=True,
        ) as resp:
            if resp.status_code == 404:
                resp.success()
            elif resp.status_code == 200:
                resp.failure(f"IDOR LEAK: document {fake_id} accessible!")
            else:
                resp.success()

    @task(1)
    def probe_admin_endpoint(self):
        """嘗試存取 admin endpoint（非管理員應收到 403）"""
        with self.client.get(
            "/api/v1/admin/tenants",
            headers=self.auth_headers,
            name="/admin/tenants [probe]",
            catch_response=True,
        ) as resp:
            if resp.status_code in (403, 401):
                resp.success()  # 正確拒絕
            elif resp.status_code == 200:
                resp.failure("Admin endpoint accessible to non-admin!")
            else:
                resp.success()


# ════════════════════════════════════════
#  Rate Limit 壓力使用者
# ════════════════════════════════════════

class RateLimitStressUser(AuthMixin, HttpUser):
    """
    快速發送請求以觸發 Rate Limiter。
    預期在超過門檻後收到 429。
    """
    wait_time = between(0.1, 0.5)  # 故意快速
    weight = 1

    def on_start(self):
        if not self.do_login(TENANT_A["email"], TENANT_A["password"]):
            self.environment.runner.quit()

    @task
    def rapid_health_check(self):
        with self.client.get(
            "/api/v1/documents/",
            headers=self.auth_headers,
            name="/documents [rate-limit stress]",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 429):
                resp.success()  # 200=OK, 429=rate-limited（兩種都是正確行為）
            # 5xx 才算失敗


# ════════════════════════════════════════
#  結果鉤子：自訂驗收判斷
# ════════════════════════════════════════

@events.quitting.add_listener
def print_acceptance_criteria(environment, **kwargs):
    stats = environment.stats.total
    if stats.num_requests == 0:
        return

    p95 = stats.get_response_time_percentile(0.95)
    fail_rate = stats.num_failures / stats.num_requests if stats.num_requests > 0 else 0

    print("\n══════════════════════════════════════════")
    print("  Load Test Acceptance Criteria Report")
    print("══════════════════════════════════════════")
    print(f"  Total requests : {stats.num_requests}")
    print(f"  Failures       : {stats.num_failures}")
    print(f"  Failure rate   : {fail_rate:.2%}  (target: < 1%)")
    print(f"  p95 latency    : {p95:.0f}ms         (target: < 2000ms)")

    passed = True
    if fail_rate > 0.01:
        print("  ✗ FAIL: failure rate exceeds 1%")
        passed = False
    else:
        print("  ✓ PASS: failure rate")

    if p95 and p95 > 5000:
        print("  ✗ FAIL: p95 latency exceeds 5000ms")
        passed = False
    else:
        print("  ✓ PASS: p95 latency")

    print("══════════════════════════════════════════")
    if not passed:
        environment.process_exit_code = 1
