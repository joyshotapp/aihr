# Custom Domain SSL Automation

UniHR now supports asynchronous SSL issuance for verified tenant custom domains.

## How It Works

1. Tenant admin adds a custom domain.
2. Tenant admin completes TXT verification.
3. Backend marks the domain as `ready` and, when enabled, automatically queues an SSL provisioning task.
4. Celery worker runs the configured certificate command.
5. On success, the domain moves to `provisioned` and becomes the tenant's active custom domain.

## Required Environment Variables

Set these in production:

```env
CUSTOM_DOMAIN_SSL_AUTO_REQUEST=true
CUSTOM_DOMAIN_SSL_COMMAND_TEMPLATE=/usr/local/bin/provision-custom-domain-cert {domain}
CUSTOM_DOMAIN_SSL_RELOAD_COMMAND=docker compose exec gateway nginx -s reload
CUSTOM_DOMAIN_SSL_TIMEOUT_SECONDS=600
```

## Command Requirements

- `CUSTOM_DOMAIN_SSL_COMMAND_TEMPLATE` must be an executable command template.
- `{domain}` is replaced with the verified hostname.
- The command should exit with status `0` on success and non-zero on failure.
- If you need Certbot, wrap it in a script such as `/usr/local/bin/provision-custom-domain-cert` and keep the API process free of deployment-specific shell logic.

## UI / API Behavior

- The custom domain page shows `ready`, `provisioning`, `provisioned`, and `failed` states.
- Admins can manually retry certificate issuance from the UI.
- Failure output is persisted to `ssl_last_error` for debugging.

## Operational Notes

- Celery workers must have access to the certificate toolchain used by your command.
- If your reverse proxy needs a reload after certificate issuance, set `CUSTOM_DOMAIN_SSL_RELOAD_COMMAND`.
- Without `CUSTOM_DOMAIN_SSL_COMMAND_TEMPLATE`, domains can still be DNS-verified but will remain waiting for SSL.