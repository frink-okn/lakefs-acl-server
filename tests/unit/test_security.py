
import pytest
from fastapi import HTTPException
import security
import os

def test_encryption_decryption():
    """Verify standard encryption and decryption cycle"""
    original = "my-secret-password-123"
    encrypted = security.encrypt_secret(original)
    
    assert encrypted != original
    assert len(encrypted) > 0
    
    decrypted = security.decrypt_secret(encrypted)
    assert decrypted == original

def test_decrypt_invalid_token():
    """Verify error handling for invalid ciphertext"""
    with pytest.raises(HTTPException) as excinfo:
        security.decrypt_secret("invalid-fernet-token")
    
    assert excinfo.value.status_code == 500
    assert "Decryption failed" in excinfo.value.detail

@pytest.mark.asyncio
async def test_verify_api_token_valid():
    """Verify token acceptor"""
    token = security.API_TOKEN
    header = f"Bearer {token}"
    result = await security.verify_api_token(header)
    assert result == token

@pytest.mark.asyncio
async def test_verify_api_token_invalid():
    """Verify rejection of invalid token"""
    with pytest.raises(HTTPException) as excinfo:
        await security.verify_api_token("Bearer invalid-token")
    
    assert excinfo.value.status_code == 403

@pytest.mark.asyncio
async def test_verify_api_token_missing():
    """Verify rejection of missing/empty token"""
    with pytest.raises(HTTPException) as excinfo:
        await security.verify_api_token(None)
    
    assert excinfo.value.status_code == 403
