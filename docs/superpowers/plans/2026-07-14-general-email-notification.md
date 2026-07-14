# General Email Notification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a backend-only, database-backed email verification system for registration and password reset while retaining violation email notifications.

**Architecture:** A reusable SMTP provider and template mail service send all email and write non-sensitive delivery logs. A focused verification-code service stores salted code hashes in SQL, enforces expiry/cooldown/attempt limits, and exposes atomic consume operations to the auth API.

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy 2, Alembic, Pydantic 2, python-jose, bcrypt, pytest.

## Global Constraints

- Backend only; do not modify `smart-traffic-frontend`.
- Email is normalized with `strip().lower()`, required for every user, and globally unique.
- Codes are 6 digits, valid for 600 seconds, have a 60-second resend cooldown, allow 5 failed attempts, and are isolated by purpose.
- Store only salted code hashes; never log code plaintext, SMTP credentials, or rendered auth email bodies.
- Password resets, self-service password changes, and admin password changes increment `auth_version` so old JWTs fail.
- Password-reset code requests always return the same `202` response.
- Follow red-green-refactor for every production change.
- Preserve existing uncommitted changes in `backend/app/services/review_service.py` and `backend/tests/services/test_review_service.py`.

---

### Task 1: Persistence Model, Configuration, and Migration

**Files:**
- Create: `backend/app/models/email_verification.py`
- Create: `backend/alembic/versions/20260714_120000_add_email_verification.py`
- Modify: `backend/app/models/user.py`
- Modify: `backend/app/models/violation.py`
- Modify: `backend/app/models/__init__.py`
- Modify: `backend/app/core/config.py`
- Modify: `backend/tests/test_migrations.py`
- Create: `backend/tests/core/test_models_email_verification.py`

**Interfaces:**
- Produces: `EmailVerificationCode(email, purpose, code_hash, attempt_count, expires_at, used_at)`.
- Produces: `User.auth_version: int`, non-null unique `User.email`.
- Produces: nullable `Notification.violation_id` and `Notification.template_code`.
- Produces settings `SMTP_SECURITY`, `SMTP_TIMEOUT_SECONDS`, `EMAIL_CODE_TTL_SECONDS`, `EMAIL_CODE_RESEND_SECONDS`, `EMAIL_CODE_MAX_ATTEMPTS`.

- [ ] **Step 1: Write failing model and migration tests**

```python
def test_email_verification_model_defaults(db):
    code = EmailVerificationCode(
        email="person@example.com", purpose="register", code_hash="hash",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
    )
    db.add(code)
    db.commit()
    assert code.attempt_count == 0
    assert code.used_at is None

def test_alembic_has_single_head():
    assert _script_directory().get_heads() == ["20260714_120000"]
```

Add a migration test that builds minimal `users` and `notifications` tables, runs the new revision with patched `op`, and asserts `auth_version`, unique/non-null email, nullable `violation_id`, `template_code`, and `email_verification_codes` exist. Add duplicate/null preflight cases that assert `RuntimeError` includes an actionable email cleanup message.

- [ ] **Step 2: Run tests and verify RED**

Run: `cd backend && uv run pytest tests/core/test_models_email_verification.py tests/test_migrations.py -v`

Expected: FAIL because `EmailVerificationCode` and revision `20260714_120000` do not exist.

- [ ] **Step 3: Implement models, settings, and migration**

Create the model with this public shape:

```python
class EmailVerificationCode(Base):
    __tablename__ = "email_verification_codes"
    __table_args__ = (
        CheckConstraint("purpose IN ('register', 'password_reset')", name="ck_email_code_purpose"),
        Index("ix_email_codes_email_purpose_created", "email", "purpose", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255))
    purpose: Mapped[str] = mapped_column(String(32))
    code_hash: Mapped[str] = mapped_column(String(255))
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
```

Update `User.email` to `nullable=False, unique=True`, add `auth_version` with default 0, and update notification columns. The migration must use `down_revision = "b4f2c8d6a109"`, preflight existing email data before making it non-null/unique, and use Alembic batch operations so SQLite migration tests work.

- [ ] **Step 4: Run focused tests and verify GREEN**

Run: `cd backend && uv run pytest tests/core/test_models_email_verification.py tests/test_migrations.py -v`

Expected: PASS.

- [ ] **Step 5: Commit Task 1**

```bash
git add backend/app/models backend/app/core/config.py backend/alembic/versions/20260714_120000_add_email_verification.py backend/tests/core/test_models_email_verification.py backend/tests/test_migrations.py
git commit -m "feat(email): add verification persistence"
```

### Task 2: Standards-Compliant SMTP Provider

**Files:**
- Modify: `backend/app/services/notification_provider.py`
- Modify: `backend/tests/services/test_notification_provider.py`

**Interfaces:**
- Consumes: SMTP settings from Task 1.
- Produces: `EmailSmtpProvider.send(to_email: str, subject: str, body: str) -> SendResult` with MIME, `starttls|ssl|none`, timeout, and sanitized errors.

- [ ] **Step 1: Write failing provider tests**

Use fake `SMTP` and `SMTP_SSL` context managers and assert:

```python
message = email.message_from_bytes(fake.sent_message)
assert str(make_header(decode_header(message["Subject"]))) == "中文主题"
assert message.get_payload(decode=True).decode(message.get_content_charset()) == "中文正文\n"
assert fake.starttls_called is True
assert fake.login_args == ("smtp-user", "smtp-pass")
```

Add separate tests for SSL selection, no-security selection, configured timeout, no login without `SMTP_USER`, invalid `SMTP_SECURITY`, missing config, and a connection exception that returns a stable error category without the raw credential.

- [ ] **Step 2: Run provider tests and verify RED**

Run: `cd backend && uv run pytest tests/services/test_notification_provider.py -v`

Expected: FAIL because the provider currently builds raw headers and has no SSL/security-mode support.

- [ ] **Step 3: Implement minimal provider behavior**

Construct mail using:

```python
message = EmailMessage()
message["From"] = settings.SMTP_FROM
message["To"] = to_email
message["Subject"] = subject
message.set_content(body)
```

Select `smtplib.SMTP_SSL` only for `ssl`; otherwise use `smtplib.SMTP` and call `starttls()` only for `starttls`. Pass `timeout=settings.SMTP_TIMEOUT_SECONDS`. Map failures to stable values such as `smtp_connection_failed`, `smtp_auth_failed`, and `smtp_send_failed`; do not return `str(exc)`.

- [ ] **Step 4: Run provider tests and verify GREEN**

Run: `cd backend && uv run pytest tests/services/test_notification_provider.py -v`

Expected: PASS.

- [ ] **Step 5: Commit Task 2**

```bash
git add backend/app/services/notification_provider.py backend/tests/services/test_notification_provider.py
git commit -m "feat(email): harden SMTP provider"
```

### Task 3: Generic Template Mail Service and Seed Templates

**Files:**
- Modify: `backend/app/services/notification_service.py`
- Modify: `backend/tests/services/test_notification_service.py`
- Modify: `backend/seed_data.py`
- Modify: `backend/tests/test_seed_data.py`

**Interfaces:**
- Consumes: `NotificationProvider.send` and generalized `Notification` model.
- Produces: `NotificationService.send_template(template_code: str, recipient: str, context: dict[str, object], *, owner_id: int | None = None, violation_id: int | None = None, audit_content: str | None = None) -> Notification`.
- Preserves: `send_violation_notification(violation: Violation, owner_email: str | None) -> Notification`.

- [ ] **Step 1: Write failing generic-mail tests**

```python
def test_send_template_logs_redacted_auth_content(db):
    db.add(NotificationTemplate(
        code="register_email_code", subject_template="验证码",
        body_template="验证码 {code}", channel="email",
    ))
    db.commit()
    provider = FakeNotificationProvider()
    result = NotificationService(db, provider).send_template(
        "register_email_code", "u@example.com", {"code": "123456"},
        audit_content="注册邮箱验证码邮件",
    )
    assert result.status == "sent"
    assert result.template_code == "register_email_code"
    assert "123456" not in result.content
    assert provider.sent[0][2] == "验证码 123456"
```

Add tests for missing/disabled templates, bad template variables, provider failure, and a regression test proving violation mail still records full non-secret content.

- [ ] **Step 2: Run service tests and verify RED**

Run: `cd backend && uv run pytest tests/services/test_notification_service.py tests/test_seed_data.py -v`

Expected: FAIL because `send_template` and auth templates do not exist.

- [ ] **Step 3: Implement generic service and idempotent seeds**

Implement the exact signature above. Resolve only enabled `channel="email"` templates. Record `template_missing`, `template_render_failed`, and provider results without raising raw formatting/SMTP exceptions. Refactor `send_violation_notification` to call `send_template` and preserve `no_recipient` behavior. Seed these templates:

```python
AUTH_EMAIL_TEMPLATES = {
    "register_email_code": (
        "【交通违章智能管理平台】注册验证码",
        "您的注册验证码是 {code}，10 分钟内有效。请勿向他人泄露。",
    ),
    "password_reset_email_code": (
        "【交通违章智能管理平台】密码重置验证码",
        "您的密码重置验证码是 {code}，10 分钟内有效。若非本人操作，请忽略。",
    ),
}
```

- [ ] **Step 4: Run service and seed tests and verify GREEN**

Run: `cd backend && uv run pytest tests/services/test_notification_service.py tests/test_seed_data.py -v`

Expected: PASS.

- [ ] **Step 5: Commit Task 3**

```bash
git add backend/app/services/notification_service.py backend/tests/services/test_notification_service.py backend/seed_data.py backend/tests/test_seed_data.py
git commit -m "feat(email): add template mail service"
```

### Task 4: Database-Backed Verification Code Service

**Files:**
- Create: `backend/app/services/email_verification_service.py`
- Create: `backend/tests/services/test_email_verification_service.py`

**Interfaces:**
- Consumes: `NotificationService.send_template` and `EmailVerificationCode`.
- Produces: `normalize_email(email: str) -> str`.
- Produces: `EmailVerificationService.send_code(email: str, purpose: str) -> Notification`.
- Produces: `EmailVerificationService.consume_code(email: str, purpose: str, code: str) -> EmailVerificationCode`.
- Produces exceptions `EmailCodeCooldown`, `EmailDeliveryFailed`, and `InvalidEmailCode` for API mapping.

- [ ] **Step 1: Write failing verification service tests**

Cover one behavior per test:

```python
def test_send_code_stores_hash_not_plaintext(db, monkeypatch):
    monkeypatch.setattr("app.services.email_verification_service.secrets.randbelow", lambda _: 23456)
    service.send_code(" User@Example.COM ", "register")
    saved = db.query(EmailVerificationCode).one()
    assert saved.email == "user@example.com"
    assert saved.code_hash != "123456"
    assert verify_password("123456", saved.code_hash)

def test_consume_code_is_one_time(db):
    service.send_code("u@example.com", "register")
    service.consume_code("u@example.com", "register", captured_code)
    with pytest.raises(InvalidEmailCode):
        service.consume_code("u@example.com", "register", captured_code)
```

Also test exact TTL, cooldown, purpose isolation, expiration, attempts 1 through 5, old-code invalidation only after successful replacement delivery, delivery failure preserving the previous code, and unsupported purpose.

- [ ] **Step 2: Run verification tests and verify RED**

Run: `cd backend && uv run pytest tests/services/test_email_verification_service.py -v`

Expected: FAIL because the service module does not exist.

- [ ] **Step 3: Implement minimal verification service**

Generate with `f"{secrets.randbelow(1_000_000):06d}"`, hash with existing `hash_password`, and compare with `verify_password`. Query the latest record by `(email, purpose, created_at DESC)`. Use timezone-aware UTC datetimes and normalize SQLite-returned naive datetimes before comparison. Commit failed-attempt increments before raising `InvalidEmailCode`; callers own the successful consume transaction so user changes and `used_at` commit atomically.

- [ ] **Step 4: Run verification tests and verify GREEN**

Run: `cd backend && uv run pytest tests/services/test_email_verification_service.py -v`

Expected: PASS.

- [ ] **Step 5: Commit Task 4**

```bash
git add backend/app/services/email_verification_service.py backend/tests/services/test_email_verification_service.py
git commit -m "feat(email): add verification code service"
```

### Task 5: JWT Authentication Versioning

**Files:**
- Modify: `backend/app/core/security.py`
- Modify: `backend/app/core/deps.py`
- Modify: `backend/app/api/v1/auth.py`
- Modify: `backend/app/services/user_service.py`
- Modify: `backend/app/schemas/user.py`
- Modify: `backend/tests/core/test_security.py`
- Modify: `backend/tests/core/test_deps.py`
- Modify: `backend/tests/api/test_auth.py`
- Modify: `backend/tests/api/test_users_api.py`
- Modify: `backend/tests/services/test_user_service.py`
- Modify: `backend/tests/conftest.py`

**Interfaces:**
- Produces: `create_access_token(subject: str, role: str, auth_version: int = 0, expires_minutes: int | None = None) -> str`.
- Enforces: `get_current_user` rejects JWT `auth_version` unequal to `User.auth_version`.

- [ ] **Step 1: Write failing token invalidation tests**

```python
def test_get_current_user_rejects_stale_auth_version(db, citizen_user):
    token = create_access_token(
        subject=str(citizen_user.id), role="citizen", auth_version=0,
    )
    citizen_user.auth_version = 1
    db.commit()
    with pytest.raises(HTTPException) as exc:
        get_current_user(token=token, db=db)
    assert exc.value.status_code == 401
```

Add API tests proving self-service password change and admin password change invalidate headers created before the change. Update all token fixtures to pass the user's current version. Update user fixtures and admin-create request bodies so every created user has a unique email.

- [ ] **Step 2: Run focused auth tests and verify RED**

Run: `cd backend && uv run pytest tests/core/test_security.py tests/core/test_deps.py tests/api/test_auth.py tests/services/test_user_service.py tests/api/test_users_api.py -v`

Expected: FAIL because tokens do not carry or enforce `auth_version`.

- [ ] **Step 3: Implement token versioning and email invariants**

JWT payload must include `auth_version`. Login signs the current value. `get_current_user` treats a missing claim as 0 for backward compatibility, then compares it to the database. Both password mutation paths increment the user's version. Normalize email in `UserService`, reject duplicate emails with `409`, require email in `UserCreateIn`, and map database uniqueness races to the same `409` response.

- [ ] **Step 4: Run focused auth tests and verify GREEN**

Run: `cd backend && uv run pytest tests/core/test_security.py tests/core/test_deps.py tests/api/test_auth.py tests/services/test_user_service.py tests/api/test_users_api.py -v`

Expected: PASS.

- [ ] **Step 5: Commit Task 5**

```bash
git add backend/app/core/security.py backend/app/core/deps.py backend/app/api/v1/auth.py backend/app/services/user_service.py backend/app/schemas/user.py backend/tests/core backend/tests/api/test_auth.py backend/tests/api/test_users_api.py backend/tests/services/test_user_service.py backend/tests/conftest.py
git commit -m "feat(auth): invalidate stale tokens after password changes"
```

### Task 6: Registration Verification and Password Reset API

**Files:**
- Modify: `backend/pyproject.toml`
- Modify: `backend/uv.lock`
- Modify: `backend/app/schemas/auth.py`
- Modify: `backend/app/api/v1/auth.py`
- Modify: `backend/app/core/deps.py`
- Modify: `backend/tests/api/test_auth.py`
- Modify: `backend/tests/api/test_review_flow_integration.py`

**Interfaces:**
- Consumes: `EmailVerificationService`, `NotificationProvider`, `normalize_email`, and token versioning.
- Produces endpoints `POST /auth/register/email-code`, `POST /auth/password-reset/email-code`, and `POST /auth/password-reset`.
- Changes: `RegisterRequest.email: EmailStr` and `RegisterRequest.verification_code: str` are required.

- [ ] **Step 1: Write failing endpoint tests**

Override `get_notification_provider` with a shared `FakeNotificationProvider`. Seed auth templates and extract the 6-digit code from `provider.sent[-1][2]` only inside tests.

```python
def test_register_with_emailed_code_creates_normalized_unique_user(client, db, seeded_roles):
    send = client.post("/api/v1/auth/register/email-code", json={"email": " New@Example.COM "})
    assert send.status_code == 202
    code = extract_code(fake_provider.sent[-1][2])
    response = client.post("/api/v1/auth/register", json={
        "username": "newuser", "password": "pass1234",
        "email": " New@Example.COM ", "verification_code": code,
    })
    assert response.status_code == 201
    assert db.query(User).filter_by(username="newuser").one().email == "new@example.com"
```

Add tests for existing email `409`, cooldown `429`, delivery failure `503`, missing/invalid/expired/used/wrong-purpose registration codes, duplicate email race mapping, uniform password-reset request responses for unknown/disabled/cooldown/provider failure, successful reset, incorrect/expired/used code, old password rejection, and old JWT invalidation.

- [ ] **Step 2: Run API tests and verify RED**

Run: `cd backend && uv run pytest tests/api/test_auth.py -v`

Expected: FAIL with 404 for the three new endpoints and schema mismatch for registration.

- [ ] **Step 3: Implement schemas, dependency helper, and endpoints**

Add `email-validator>=2.1` to the backend dependencies and refresh `uv.lock`, because Pydantic `EmailStr` delegates standards-aware address validation to that package.

Define:

```python
class EmailCodeRequest(BaseModel):
    email: EmailStr

class RegisterRequest(BaseModel):
    username: str
    password: str
    phone: str | None = None
    email: EmailStr
    verification_code: str

class PasswordResetRequest(BaseModel):
    email: EmailStr
    verification_code: str
    new_password: str
```

Add a dependency or local factory that constructs `NotificationService(db, provider)` and `EmailVerificationService`. Registration checks username/email conflicts, consumes `register`, adds the user, and commits once. Password reset code requests always return `202`; for active known users they attempt delivery and suppress cooldown/delivery details after logging. Reset locks the user, consumes `password_reset`, updates hash, increments `auth_version`, and commits once.

- [ ] **Step 4: Run auth and review integration tests and verify GREEN**

Run: `cd backend && uv run pytest tests/api/test_auth.py tests/api/test_review_flow_integration.py -v`

Expected: PASS.

- [ ] **Step 5: Commit Task 6**

```bash
git add backend/pyproject.toml backend/uv.lock backend/app/schemas/auth.py backend/app/api/v1/auth.py backend/app/core/deps.py backend/tests/api/test_auth.py backend/tests/api/test_review_flow_integration.py
git commit -m "feat(auth): add email verification and password reset APIs"
```

### Task 7: Regression, Migration, and Documentation Verification

**Files:**
- Modify: `README.md`
- Modify: `docs/API-完整接口文档.md`
- Modify: any backend tests that create users without unique required emails, without changing their tested behavior.

**Interfaces:**
- Verifies all interfaces produced by Tasks 1-6.

- [ ] **Step 1: Run the full backend suite to discover compatibility failures**

Run: `cd backend && uv run pytest -v`

Expected: Any remaining failures are limited to fixtures/request bodies that violate the new required unique-email invariant; no implementation behavior failures remain.

- [ ] **Step 2: Update affected tests and API documentation**

Give every test-created user a deterministic unique email. Document the three new endpoints, the required registration code, response codes, SMTP environment variables, and the password-reset non-enumeration behavior. Do not document or expose test-only code extraction.

- [ ] **Step 3: Run static and migration checks**

Run: `cd backend && uv run pytest tests/test_migrations.py tests/services/test_notification_provider.py tests/services/test_notification_service.py tests/services/test_email_verification_service.py tests/api/test_auth.py -v`

Expected: PASS with no warnings introduced by this feature.

- [ ] **Step 4: Run the complete regression suite**

Run: `cd backend && uv run pytest -q`

Expected: All tests pass.

- [ ] **Step 5: Review secret handling and diff scope**

Run: `rg -n "SMTP_PASSWORD|verification_code|code_hash" backend/app backend/tests README.md docs/API-完整接口文档.md`

Expected: `SMTP_PASSWORD` is read only from settings; production logging and notification content contain no code plaintext; no frontend files changed. Run `git diff --check` and inspect `git status --short` to confirm the user's pre-existing files remain preserved.

- [ ] **Step 6: Commit Task 7**

```bash
git add README.md docs/API-完整接口文档.md backend/tests
git commit -m "docs(email): document verification and reset flow"
```

## Final Verification

- [ ] Run `cd backend && uv run pytest -q` and record the exact passing count.
- [ ] Run `git diff --check` and confirm no whitespace errors.
- [ ] Confirm `git status --short` shows only the user's pre-existing unrelated modifications, if any.
- [ ] Confirm no file under `smart-traffic-frontend` changed.
- [ ] Confirm real SMTP delivery was not attempted unless explicit credentials were supplied for a manual environment test.
