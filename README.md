# LakeFS Remote Authentication & ACL Server

This project implements a custom Remote Authenticator for LakeFS, enforcing Access Control Lists (ACLs) via an external `acl-server`. It provides centralized user management, credential storage with encryption at rest, and policy-based access control.

## Project Structure

- **acl_server/**: FastAPI application handling authentication and authorization requests.
- **docker-compose.yml**: Orchestration for LakeFS, PostgreSQL, ACL Server, and S5cmd (for testing).
- **tests/**:
  - **unit/**: Python `pytest` suite for ACL server logic.
  - **e2e/**: Bash scripts for end-to-end integration testing.

## Prerequisites

- Docker
- Docker Compose

## Quick Start

1. **Configuration**:
   Copy the template configuration file:
   ```bash
   cp .env-template .env
   ```
   Edit `.env` and initialize the secrets. For security, ensure `LAKEFS_AUTH_ENCRYPT_SECRET_KEY` is a strong random string.

2. **Run the Stack**:
   Start the services:
   ```bash
   docker-compose up -d --build
   ```

3. **Verify Status**:
   Ensure all containers are healthy:
   ```bash
   docker-compose ps
   ```

## Configuration

Environment variables are managed in `.env`.

- `ACL_API_TOKEN`: Shared secret for service-to-service authentication between scripts/tests and the ACL server.
- `LAKEFS_AUTH_API_TOKEN`: Shared secret for LakeFS to authenticate against the ACL server.
- `ACL_ENCRYPTION_KEY`: 32-byte URL-safe base64 key for encrypting secrets at rest in the ACL database.
- `LAKEFS_AUTH_ENCRYPT_SECRET_KEY`: Secret key used by LakeFS for signing session cookies.

## Development

### Running Unit Tests

Unit tests cover the ACL server's internal logic, including encryption and policy evaluation.

1. Install dependencies:
   ```bash
   pip install -r acl_server/requirements.txt
   pip install pytest pytest-asyncio httpx
   ```

2. Run tests:
   ```bash
   pytest tests/unit
   ```

### Running E2E Tests

End-to-End tests verify the full flow: LakeFS setup -> ACL Sync -> S3 Access verification.

1. Ensure the Docker stack is running.
2. Run the test script:
   ```bash
   ./tests/e2e/e2e.sh
   ```

## Architecture

1. **LakeFS** is configured to delegate authentication to the `acl-server` via the Remote Authenticator protocol.
2. **ACL Server** manages:
   - **Users**: Identities syncing with LakeFS.
   - **Credentials**: Access Keys and Secret Keys (encrypted at rest).
   - **Policies**: Allow/Deny rules based on resources and actions.
3. **PostgreSQL**: Persistent storage for LakeFS metadata.
4. **SQLite/PostgreSQL**: Storage for ACL data (configured via `DATABASE_CONNECTION_STRING`).

## Security Notes

- **Encryption at Rest**: Secret Access Keys are encrypted using Fernet (AES-GCM) before being stored in the database.
- **Session Security**: LakeFS session cookies are signed with a securely generated key defined in `.env`.
- **API Security**: All protected API endpoints require a Bearer token.
