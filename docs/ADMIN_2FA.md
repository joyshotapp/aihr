# Admin 2FA

UniHR now supports TOTP-based 2FA for `owner`, `admin`, and platform superuser accounts.

## Flow

1. Sign in to the company admin area.
2. Open the `安全` tab in company settings.
3. Generate a TOTP secret.
4. Add the secret to an authenticator app.
5. Confirm with a 6-digit code.
6. Future logins require both password and TOTP.

## Supported Authenticator Apps

- Google Authenticator
- Microsoft Authenticator
- 1Password
- Authy-compatible TOTP apps

## API Endpoints

- `GET /api/v1/auth/mfa/status`
- `POST /api/v1/auth/mfa/setup`
- `POST /api/v1/auth/mfa/enable`
- `POST /api/v1/auth/mfa/disable`
- `POST /api/v1/auth/mfa/verify-login`

## Notes

- Current implementation stores the shared TOTP secret in the application database.
- For stricter enterprise controls, pair this with the planned BYOK / field-level encryption work.