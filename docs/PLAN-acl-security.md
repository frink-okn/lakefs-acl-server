# Security Hardening Plan: ACL Server

## 1. Goal
Harden the Python ACL Server to secure sensitive data (Access Keys) and restrict API access, adhering to security best practices for an internal Kubernetes deployment.

## 2. Security Architecture

### A. Deployment Context
- **Environment**: Kubernetes (Internal Network).
- **Exposure**: Private (Cluster-only). LakeFS connects via internal K8s DNS.
- **TLS**: Terminated at Ingress/Mesh level (not application level).

### B. Encryption at Rest (P0 - Critical)
- **Algorithm**: AES-GCM (via `cryptography` Fernet).
- **Key Management**: 
  - `ACL_ENCRYPTION_KEY` environment variable.
  - 32-byte URL-safe base64 string.
- **Scope**: Encrypt `secret_access_key` column in `auth_credentials` table (or equivalent).
- **Workflow**:
    - **Write**: `encrypt(raw_secret, key)` -> Database
    - **Read**: `decrypt(db_blob, key)` -> API Response
    - **Constraint**: `access_key_id` remains plaintext for lookups.

### C. API Authentication (Service-to-Service)
- **Mechanism**: Shared Secret Token (Bearer Token).
- **Configuration**: `ACL_API_TOKEN` environment variable.
- **Enforcement**: Global FastAPI Dependency (`Depends(verify_api_token)`).
- **Client**: LakeFS configured with `auth.api.token`.

## 3. Implementation Steps

### Phase 1: Dependencies & Configuration
- [ ] Verify `cryptography` in `requirements.txt` (Already present).
- [ ] Create `security.py` module:
    - [`Cipher`](file:///c:/Users/kebedey/projects/lakefs-auth/acl_server/security.py) wrapper for Fernet.
    - `get_api_token()` config loader.
    - `verify_api_token` dependency logic.

### Phase 2: Encryption Logic (P0)
- [ ] Refactor [`credentials.py`](file:///c:/Users/kebedey/projects/lakefs-auth/acl_server/routers/credentials.py):
    - `create_credentials`:
        - Generate `raw_secret`.
        - Encrypt `raw_secret` -> `encrypted_secret`.
        - Store `encrypted_secret` in DB.
        - Return `raw_secret` in response (one-time show).
    - `get_credentials`:
        - Retrieve `encrypted_secret` from DB.
        - Decrypt -> `raw_secret`.
        - Return `raw_secret`.
- [ ] Refactor [`import_credentials.py`](file:///c:/Users/kebedey/projects/lakefs-auth/acl_server/scripts/import_credentials.py):
    - Encrypt secrets before inserting into DB.

### Phase 3: API Security Enforcement
- [ ] Apply `Depends(verify_api_token)` to [`main.py`](file:///c:/Users/kebedey/projects/lakefs-auth/acl_server/main.py) to protect all endpoints (or via `APIRouter` dependencies).
- [ ] Verify `verify_lakefs_login.ps1` and other scripts pass credentials correctly.

### Phase 4: Verification (Phase X)
- [ ] **Manual Audit**: Check `security.py` for hardcoded keys (FAIL if found).
- [ ] **Script**: Verify Database content is encrypted (not human readable).
    - Run `sqlite3` or `psql` to inspect `access_secret_access_key`.
- [ ] **Script**: Valid Token -> 200 OK.
- [ ] **Script**: Invalid/No Token -> 401 Unauthorized.
- [ ] **E2E**: LakeFS successfully boots and authenticates.

## 4. Future Considerations (Post-Implementation)
- **Audit Logging**: Track who created/deleted credentials (middleware).
- **Key Rotation**: Script to re-encrypt database with new key.
