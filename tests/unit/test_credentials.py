
import pytest
from models import User, AccessKey
import security
import time

def test_create_credentials(client, db_session, valid_token):
    """Verify credential creation with encryption"""
    # Create User
    user = User(id="testuser", created_at=int(time.time()))
    db_session.add(user)
    db_session.commit()
    
    headers = {"Authorization": f"Bearer {valid_token}"}
    response = client.post(
        "/api/v1/auth/users/testuser/credentials",
        headers=headers
    )
    
    assert response.status_code == 201
    data = response.json()
    ak = data["access_key_id"]
    sk = data["secret_access_key"]
    
    # Verify DB explicitly
    cred = db_session.query(AccessKey).filter(AccessKey.access_access_key_id == ak).first()
    assert cred is not None
    # Secret in DB should NOT define original sk (it should be encrypted)
    assert cred.access_secret_access_key != sk
    assert security.decrypt_secret(cred.access_secret_access_key) == sk

def test_get_credentials(client, db_session, valid_token):
    """Verify credential retrieval and decryption"""
    # Create User and Credential directly in DB
    user = User(id="testuser", created_at=int(time.time()))
    sk_plain = "my-secret-key"
    sk_enc = security.encrypt_secret(sk_plain)
    
    cred = AccessKey(
        access_access_key_id="AKTEST123",
        access_secret_access_key=sk_enc,
        user_id="testuser",
        created_at=int(time.time())
    )
    db_session.add(user)
    db_session.add(cred)
    db_session.commit()
    
    headers = {"Authorization": f"Bearer {valid_token}"}
    response = client.get(
        "/api/v1/auth/credentials/AKTEST123",
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["access_key_id"] == "AKTEST123"
    assert data["secret_access_key"] == sk_plain

def test_create_credentials_user_not_found(client, db_session, valid_token):
    headers = {"Authorization": f"Bearer {valid_token}"}
    response = client.post(
        "/api/v1/auth/users/nonexistent/credentials",
        headers=headers
    )
    assert response.status_code == 404
