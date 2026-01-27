# Unit Testing Plan

## Goal
Create a comprehensive unit test suite for the `acl_server` to verify logic and security features.

## Scope
- **Core Logic**: `security.py`, `logic.py`
- **Routers**: `credentials.py`, `users.py`, `groups.py`, `policies.py`
- **Mocking**: Use `unittest.mock` or `pytest-mock` to mock Database sessions.

## Test Structure
Directory: `tests/unit/`

- `conftest.py`: Fixtures for mocked DB, client, etc.
- `test_security.py`: Encryption and Token verification.
- `test_logic.py`: Policy evaluation logic.
- `test_credentials.py`: Credential management.
- `test_users.py`: User management.

## Verification
- Run `pytest tests/unit`
- Ensure all tests pass.

## Tasks
- [ ] Install `pytest` (if missing).
- [ ] Create `tests/unit/conftest.py`.
- [ ] Create `tests/unit/test_security.py`.
- [ ] Create `tests/unit/test_logic.py`.
- [ ] Create `tests/unit/test_credentials.py` (Mocked).
