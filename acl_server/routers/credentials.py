from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from database import get_db
from models import AccessKey, User
from schemas import Credentials, CredentialsList, CredentialsWithSecret, Pagination, CredentialsCreation
from typing import List, Optional
import time
import secrets
import string
import security

router = APIRouter(prefix="/auth", tags=["auth"])

def generate_key_id():
    return "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(20))

def generate_secret_key():
    return "".join(secrets.choice(string.ascii_letters + string.digits + "/+") for _ in range(40))

# --- Credentials ---

@router.get("/credentials/{accessKeyId}", response_model=CredentialsWithSecret)
def get_credentials(accessKeyId: str, db: Session = Depends(get_db)):
    cred = db.query(AccessKey).filter(AccessKey.access_access_key_id == accessKeyId).first()
    if not cred:
        raise HTTPException(status_code=404, detail="Credentials not found")
        
    # Decrypt the secret key before returning
    try:
        decrypted_secret = security.decrypt_secret(cred.access_secret_access_key)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to decrypt credentials")

    # Note: user_name required by spec, maps to user_id (which is username in our model)
    return CredentialsWithSecret(
        access_key_id=cred.access_access_key_id,
        secret_access_key=decrypted_secret,
        creation_date=cred.created_at,
        user_id=1, # Dummy ID for deprecated integer field
        user_name=cred.user_id 
    )

@router.get("/users/{userId}/credentials", response_model=CredentialsList)
def list_user_credentials(
    userId: str,
    prefix: str = "",
    after: str = "",
    amount: int = 100,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == userId).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    query = db.query(AccessKey).filter(AccessKey.user_id == userId)
    if prefix:
        query = query.filter(AccessKey.access_access_key_id.startswith(prefix))
        
    query = query.order_by(AccessKey.access_access_key_id)
    
    if after:
        query = query.filter(AccessKey.access_access_key_id > after)
        
    results = query.limit(amount + 1).all()
    has_more = len(results) > amount
    results = results[:amount]
    next_offset = results[-1].access_access_key_id if results else ""
    
    return {
        "pagination": {
            "has_more": has_more,
            "max_per_page": amount,
            "results": len(results),
            "next_offset": next_offset
        },
        "results": [
            Credentials(
                access_key_id=c.access_access_key_id,
                creation_date=c.created_at
            ) for c in results
        ]
    }

@router.post("/users/{userId}/credentials", response_model=CredentialsWithSecret, status_code=status.HTTP_201_CREATED)
def create_credentials(
    userId: str, 
    credentials_in: Optional[CredentialsCreation] = None,
    access_key: Optional[str] = Query(None), 
    secret_key: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == userId).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Prefer body params, fallback to query params (backward compatibility)
    ak = None
    sk = None
    
    if credentials_in:
        ak = credentials_in.access_key_id
        sk = credentials_in.secret_access_key
        
    ak = ak or access_key or generate_key_id()
    sk = sk or secret_key or generate_secret_key()
    
    # Encrypt the secret before storing
    encrypted_sk = security.encrypt_secret(sk)
    
    if db.query(AccessKey).filter(AccessKey.access_access_key_id == ak).first():
        raise HTTPException(status_code=409, detail="Access Key already exists")

    new_cred = AccessKey(
        access_access_key_id=ak,
        access_secret_access_key=encrypted_sk,
        user_id=userId,
        created_at=int(time.time())
    )
    db.add(new_cred)
    db.commit()
    db.refresh(new_cred)
    
    return CredentialsWithSecret(
        access_key_id=new_cred.access_access_key_id,
        secret_access_key=sk, # Return raw secret one time
        creation_date=new_cred.created_at,
        user_id=1, # Dummy ID for deprecated integer field
        user_name=new_cred.user_id
    )

from fastapi import Response

@router.delete("/users/{userId}/credentials/{accessKeyId}", status_code=status.HTTP_204_NO_CONTENT)
def delete_credentials(userId: str, accessKeyId: str, db: Session = Depends(get_db)):
    # Spec says check userId and accessKeyId match?
    # Usually yes.
    cred = db.query(AccessKey).filter(AccessKey.access_access_key_id == accessKeyId, AccessKey.user_id == userId).first()
    if not cred:
         raise HTTPException(status_code=404, detail="Credentials not found")
         
    db.delete(cred)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.get("/users/{userId}/credentials/{accessKeyId}", response_model=Credentials)
def get_credentials_for_user(userId: str, accessKeyId: str, db: Session = Depends(get_db)):
    cred = db.query(AccessKey).filter(AccessKey.access_access_key_id == accessKeyId, AccessKey.user_id == userId).first()
    if not cred:
        raise HTTPException(status_code=404, detail="Credentials not found")
    
    return Credentials(
        access_key_id=cred.access_access_key_id,
        creation_date=cred.created_at
    )
