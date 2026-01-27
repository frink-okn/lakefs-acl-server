# GitHub Actions & E2E Testing Plan

## Goal
Implement a robust CI pipeline ensuring LakeFS and ACL Server integrate correctly, validated by S3 operations.

## Architecture
- **CI Runner**: GitHub Actions (Ubuntu).
- **Stack**: Docker Compose (`postgres`, `lakefs`, `acl-server`, `s5cmd`).
- **Test Logic**: Bash script (`e2e.sh`) running on the host (GitHub runner), executing commands against containers via `curl` and `docker exec`.

## Changes

### 1. Docker Compose (`docker-compose.yml`)
- **Add Service**: `s5cmd`
    - Image: `peakcom/s5cmd`
    - Entrypoint: `tail -f /dev/null` (keep alive)
    - Environment: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` (placeholders, overridden at runtime or via config), `S3_ENDPOINT_URL=http://lakefs:8000`.

### 2. E2E Script (`tests/e2e/e2e.sh`)
**Steps:**
1.  **Wait for Health**: Loop check `localhost:8000/_health` and `localhost:9000/api/v1/healthcheck`.
2.  **Setup LakeFS**: `POST /api/v1/setup_lakefs` to get Admin credentials.
3.  **Sync ACL**: `POST /auth/users` (create admin in ACL).
4.  **Create Bucket**: Use `s5cmd` (via docker exec) to create `s3://e2e-test-bucket`.
5.  **Upload/Download**: Use `s5cmd` to pipe content to a file in bucket and read it back.
    - Command: `echo "Hello" | s5cmd pipe s3://e2e-test-bucket/test.txt`
    - Verify output matches.

### 3. GitHub Workflow (`.github/workflows/ci.yml`)
- **Trigger**: Push/PR.
- **Job**:
    - Checkout.
    - Setup Python (for Unit Tests).
    - Install pip deps.
    - **Unit Tests**: `pytest tests/unit`.
    - **E2E Setup**:
        - `docker-compose up -d --build`.
        - `chmod +x tests/e2e/e2e.sh`.
    - **E2E Execution**: `./tests/e2e/e2e.sh`.

## Tasks
- [ ] Update `docker-compose.yml` (Add `s5cmd`).
- [ ] Create `tests/e2e/e2e.sh` (Bash logic).
- [ ] Create `.github/workflows/ci.yml`.
- [ ] Verify locally.
