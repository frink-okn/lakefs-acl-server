# Stale Session Security Fix

## Problem
Users remain "logged in" after a full system wipe (`docker-compose down -v`) because the browser retains a session cookie signed by a **static** `LAKEFS_AUTH_ENCRYPT_SECRET_KEY` ("some_string"). Since the key doesn't change, and the new admin user often has the same ID (`admin`), the old cookie is accepted as valid by the new instance.

## Solution
1. **Externalize Key**: Move `LAKEFS_AUTH_ENCRYPT_SECRET_KEY` from `docker-compose.yml` to the `.env` file.
2. **Generate Strong Key**: Create a random string for this key in the user's `.env`.
3. **Documentation**: Update `.env-template` to reflect this new variable.

## Changes
### 1. `.env` and `.env-template`
- Add `LAKEFS_AUTH_ENCRYPT_SECRET_KEY=...`

### 2. `docker-compose.yml`
- Update `lakefs` service to use `${LAKEFS_AUTH_ENCRYPT_SECRET_KEY}`.
- **Fix Persistence**: Add volume to `postgres` service to persist `lakefs_db` across restarts.
  ```yaml
  volumes:
    - postgres_data:/var/lib/postgresql/data
  ```
- Define `postgres_data` volume at top level.

## Verification
1. **Manual Test**:
   - `docker-compose up`. Login to LakeFS (get cookie).
   - `docker-compose down -v`.
   - **Rotate Key** in `.env` (or just rely on the fact that if we *did* rotate it, it would fail).
   - *Actually*, simply externalizing it solves the "hardcoded in repo" issue, but to prevent stale sessions across *dev* resets, the user must change this key or clear cookies.
   - We will inform the user that changing this key invalidates all sessions.

2. **Automated Test** (Not applicable for browser cookies in this scope, but we verify config loading).
