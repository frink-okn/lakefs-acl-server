
import os
from cryptography.fernet import Fernet
from fastapi import HTTPException, Security, Depends
from fastapi.security.api_key import APIKeyHeader

# Config
# Generate a key using Fernet.generate_key() if not present
ENCRYPTION_KEY = os.getenv("ACL_ENCRYPTION_KEY", Fernet.generate_key().decode())
API_TOKEN = os.getenv("ACL_API_TOKEN", "super-secret-token")

cipher = Fernet(ENCRYPTION_KEY.encode())

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

def encrypt_secret(secret: str) -> str:
    return cipher.encrypt(secret.encode()).decode()

def decrypt_secret(token: str) -> str:
    try:
        return cipher.decrypt(token.encode()).decode()
    except Exception:
        raise HTTPException(status_code=500, detail="Decryption failed")

async def verify_api_token(api_key: str = Security(api_key_header)):
    """
    Verifies the Bearer token or direct token in the Authorization header.
    LakeFS might send 'Bearer <token>' or just '<token>'.
    """
    if not api_key:
        raise HTTPException(status_code=403, detail="Missing Authorization header")
    
    # Handle "Bearer " prefix if present
    token = api_key.replace("Bearer ", "").strip()
    
    if token != API_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid API Token")
    return token
