# Helm Chart Customization Plan

## Goal
Transform the generic `lakefs-acl` helm chart into a dedicated chart for hosting the `acl-server` application.

## Changes

### 1. `values.yaml`
- Update `image` defaults.
- Add `server` section for `port: 9000`.
- Add `acl` configuration section:
  - `databaseConnectionString`
  - `apiToken` (Secret)
  - `encryptionKey` (Secret)
- Enable/Disable `secrets` creation (in case user brings their own).

### 2. `templates/secret.yaml` (New)
- Create a Kubernetes Secret resource `{{ .Release.Name }}-secrets`.
- Store `ACL_API_TOKEN` and `ACL_ENCRYPTION_KEY`.

### 3. `templates/deployment.yaml`
- Update container port to `9000`.
- Update Liveness/Readiness probes to point to `http://:9000/healthcheck` (or `/api/v1/healthcheck`).
- Inject Environment Variables:
  - `DATABASE_CONNECTION_STRING`: From values.
  - `ACL_API_TOKEN`: From Secret.
  - `ACL_ENCRYPTION_KEY`: From Secret.

### 4. `templates/service.yaml`
- Update Service port to target `9000`.

## Verification
- **Dry Run**: `helm template .` to inspect the generated manifests.
- **Lint**: `helm lint .` to check for syntax errors.
