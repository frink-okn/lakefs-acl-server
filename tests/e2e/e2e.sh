#!/bin/bash
set -e

# Configuration
LAKEFS_ENDPOINT="http://localhost:8000"
ACL_ENDPOINT="http://localhost:9000/api/v1"
ACL_API_TOKEN=${ACL_API_TOKEN:-"super-secret-token"}
S5CMD_CONTAINER="lakefs-auth-s5cmd-1"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "Waiting for services..."
until curl -s $LAKEFS_ENDPOINT/_health > /dev/null; do
  echo "Waiting for lakeFS..."
  sleep 5
done
echo -e "${GREEN}lakeFS is up!${NC}"

until curl -s $ACL_ENDPOINT/healthcheck > /dev/null; do
  echo "Waiting for ACL Server..."
  sleep 5
done
echo -e "${GREEN}ACL Server is up!${NC}"

# 1. Setup LakeFS
echo "Setting up lakeFS admin..."
# Assuming fresh start or handling 409
SETUP_RESP=$(curl -s -X POST $LAKEFS_ENDPOINT/api/v1/setup_lakefs \
  -H "Content-Type: application/json" \
  -d '{"username":"admin"}')

# Check if already setup
if echo "$SETUP_RESP" | grep -q "error"; then
   echo "lakeFS might be already setup. Proceeding... (Note: If keys are unknown, subsequent steps will fail)"
else
   # Extract keys using grep/cut (simple JSON parsing)
   ACCESS_KEY=$(echo $SETUP_RESP | grep -o '"access_key_id":"[^"]*' | cut -d'"' -f4)
   SECRET_KEY=$(echo $SETUP_RESP | grep -o '"secret_access_key":"[^"]*' | cut -d'"' -f4)
   
   if [ -z "$ACCESS_KEY" ]; then
       echo -e "${RED}Failed to extract Access Key from setup response!${NC}"
       echo "Response: $SETUP_RESP"
       exit 1
   fi

   echo -e "${GREEN}LakeFS Admin Created: $ACCESS_KEY${NC}"

   # 2. Sync to ACL
   echo "Syncing User to ACL..."
   # UserCreation schema: username, friendlyName, email
   curl -s -X POST "$ACL_ENDPOINT/auth/users" \
     -H "Authorization: Bearer $ACL_API_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "friendlyName": "Admin User", "email": "admin@example.com"}'

   echo "Syncing Credentials to ACL..."
   # Using Python for encoding to be safe
   ENCODED_SECRET=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$SECRET_KEY'))")
   
   curl -s -X POST "$ACL_ENDPOINT/auth/users/admin/credentials?access_key=$ACCESS_KEY&secret_key=$ENCODED_SECRET" \
     -H "Authorization: Bearer $ACL_API_TOKEN"
     
   echo -e "${GREEN}Credentials Synced!${NC}"
   
   # Export for s5cmd usage
   export AWS_ACCESS_KEY_ID=$ACCESS_KEY
   export AWS_SECRET_ACCESS_KEY=$SECRET_KEY
fi

# 3. Validate LakeFS Flow via lakectl + s5cmd
echo "Validating LakeFS Flow..."

# Find actual containers
S5CMD_CONTAINER=$(docker ps -qf "ancestor=peakcom/s5cmd" | head -n 1)
LAKEFS_CONTAINER=$(docker ps -qf "name=lakefs-auth-lakefs-1" | head -n 1) # Try predictable name
if [ -z "$LAKEFS_CONTAINER" ]; then
    LAKEFS_CONTAINER=$(docker ps -qf "ancestor=treeverse/lakefs:latest" | head -n 1)
fi

if [ -z "$S5CMD_CONTAINER" ] || [ -z "$LAKEFS_CONTAINER" ]; then
    echo -e "${RED}Containers not found! S5: $S5CMD_CONTAINER, LFS: $LAKEFS_CONTAINER${NC}"
    exit 1
fi

echo "Using s5cmd container: $S5CMD_CONTAINER"
echo "Using lakefs container: $LAKEFS_CONTAINER"

# Lakectl Env Vars for non-interactive use
# We pass them to docker exec
LAKECTL_ENV="-e LAKECTL_SERVER_ENDPOINT_URL=http://127.0.0.1:8000/api/v1 -e LAKECTL_CREDENTIALS_ACCESS_KEY_ID=$ACCESS_KEY -e LAKECTL_CREDENTIALS_SECRET_ACCESS_KEY=$SECRET_KEY"

# Create Repository
echo "Creating repository 'e2e-repo'..."
# We use 'bash -c' to ensure env vars are picked up if using lakectl binary directly, 
# but docker exec -e should set them for the process.
docker exec $LAKECTL_ENV $LAKEFS_CONTAINER lakectl repo create lakefs://e2e-repo local://e2e-repo

# Upload Object (to main branch)
echo "Uploading object via s5cmd..."
docker exec -e AWS_ACCESS_KEY_ID=$ACCESS_KEY -e AWS_SECRET_ACCESS_KEY=$SECRET_KEY \
    $S5CMD_CONTAINER sh -c "echo 'Hello E2E' | /s5cmd --endpoint-url http://lakefs:8000 pipe s3://e2e-repo/main/hello.txt"

# Commit Changes
echo "Committing changes..."
docker exec $LAKECTL_ENV $LAKEFS_CONTAINER lakectl commit lakefs://e2e-repo/main -m "E2E Commit"

# Download Object
echo "Downloading object via s5cmd..."
CONTENT=$(docker exec -e AWS_ACCESS_KEY_ID=$ACCESS_KEY -e AWS_SECRET_ACCESS_KEY=$SECRET_KEY \
    $S5CMD_CONTAINER /s5cmd --endpoint-url http://lakefs:8000 cat s3://e2e-repo/main/hello.txt)

if [ "$CONTENT" == "Hello E2E" ]; then
    echo -e "${GREEN}E2E SUCCESS: Content verified!${NC}"
else
    echo -e "${RED}E2E FAILED: Content mismatch. Got: '$CONTENT'${NC}"
    exit 1
fi
