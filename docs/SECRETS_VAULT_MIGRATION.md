# Secrets Management Migration Guide

## Current State

UniHR uses `.env.production` files loaded via Docker Compose `env_file` directive. All secrets (DB passwords, API keys, JWT signing keys) live as plaintext in this file on the host.

## Recommended Migration Path

### Option A: HashiCorp Vault (Self-hosted / HCP)

**Pros:** full audit trail, dynamic secrets, lease management, policy-based access.

#### Setup Steps

1. **Deploy Vault alongside existing stack:**

```yaml
# docker-compose.prod.yml — add vault service
vault:
  image: hashicorp/vault:1.15
  cap_add: [IPC_LOCK]
  volumes:
    - vault-data:/vault/file
  environment:
    VAULT_LOCAL_CONFIG: '{"storage":{"file":{"path":"/vault/file"}},"listener":{"tcp":{"address":"0.0.0.0:8200","tls_disable":1}}}'
  command: server
  ports:
    - "8200:8200"
```

2. **Initialize & unseal:**

```bash
docker exec -it vault vault operator init -key-shares=3 -key-threshold=2
docker exec -it vault vault operator unseal <key1>
docker exec -it vault vault operator unseal <key2>
```

3. **Store secrets:**

```bash
vault kv put secret/unihr/production \
  SECRET_KEY="$(openssl rand -base64 32)" \
  POSTGRES_PASSWORD="..." \
  GEMINI_API_KEY="..." \
  VOYAGE_API_KEY="..." \
  PINECONE_API_KEY="..." \
  R2_ACCESS_KEY_ID="..." \
  R2_SECRET_ACCESS_KEY="..." \
  SENDGRID_API_KEY="..."
```

4. **Application integration — use `hvac` Python client:**

```python
# app/config.py - vault-aware settings loader
import hvac

def load_vault_secrets():
    client = hvac.Client(url=os.environ.get("VAULT_ADDR", "http://vault:8200"))
    client.token = os.environ.get("VAULT_TOKEN")
    secret = client.secrets.kv.v2.read_secret_version(path="unihr/production")
    return secret["data"]["data"]
```

5. **Docker entrypoint wrapper:**

```bash
#!/bin/bash
# entrypoint.sh — fetch secrets from Vault before starting app
export $(vault kv get -format=json secret/unihr/production | jq -r '.data.data | to_entries[] | "\(.key)=\(.value)"')
exec "$@"
```

### Option B: Cloud Provider Secrets Manager

#### Linode / Akamai (current hosting)

Linode does not have a native secrets manager. Use **Akamai EdgeKV** or pair with a third-party vault.

#### AWS Secrets Manager (if migrating or hybrid)

```python
import boto3
import json

def get_secrets():
    client = boto3.client("secretsmanager", region_name="ap-northeast-1")
    resp = client.get_secret_value(SecretId="unihr/production")
    return json.loads(resp["SecretString"])
```

### Option C: Docker Swarm Secrets (Simplest)

If staying with Docker Compose, Docker Swarm secrets provide basic encryption at rest:

```yaml
# docker-compose.prod.yml
services:
  web:
    secrets:
      - db_password
      - secret_key
      - gemini_api_key

secrets:
  db_password:
    external: true
  secret_key:
    external: true
  gemini_api_key:
    external: true
```

```bash
echo "my-secret-password" | docker secret create db_password -
```

Application reads from `/run/secrets/<name>`.

## Secrets Inventory

| Secret                    | Service         | Rotation Frequency |
| ------------------------- | --------------- | ------------------ |
| SECRET_KEY                | JWT signing     | Quarterly          |
| POSTGRES_PASSWORD         | Database        | Quarterly          |
| GEMINI_API_KEY            | LLM generation  | On compromise      |
| VOYAGE_API_KEY            | Embeddings      | On compromise      |
| PINECONE_API_KEY          | Vector DB       | On compromise      |
| R2_ACCESS_KEY_ID          | Object storage  | Quarterly          |
| R2_SECRET_ACCESS_KEY      | Object storage  | Quarterly          |
| SENDGRID_API_KEY          | Email           | On compromise      |
| LLAMAPARSE_API_KEY        | Doc parsing     | On compromise      |
| GOOGLE_CLIENT_SECRET      | SSO             | Yearly             |
| MICROSOFT_CLIENT_SECRET   | SSO             | Yearly             |
| REDIS_PASSWORD            | Cache/broker    | Quarterly          |

## Migration Checklist

- [ ] Choose vault solution (A, B, or C above)
- [ ] Deploy vault infrastructure
- [ ] Import all secrets from `.env.production`
- [ ] Update application entrypoint to fetch secrets at startup
- [ ] Remove plaintext `.env.production` from host
- [ ] Verify all services start correctly with vault-sourced secrets
- [ ] Set up secret rotation schedule
- [ ] Document emergency access procedure (vault unseal keys)
- [ ] Add vault health check to monitoring stack
