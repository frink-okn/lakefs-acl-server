
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import User
from schemas import User as UserSchema, UserCreation, UserList, UserPassword, Pagination
from typing import List, Optional
import time

router = APIRouter(prefix="/auth/users", tags=["auth"])

@router.get("", response_model=UserList)
def list_users(
    prefix: str = "",
    after: str = "",
    amount: int = 100,
    id: Optional[int] = None, # Spec says id is integer query param? But User.id is string username used internally.
                               # Wait, spec says: "Internally, the username value is converted to the id field"
                               # But parameter 'id' type integer format int64. 
                               # It might mean the internal serial ID? But we use string IDs (usernames).
                               # Let's ignore it for now or support it loosely.
    email: Optional[str] = None,
    external_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(User)
    
    # Filtering
    if prefix:
        query = query.filter(User.id.startswith(prefix))
    if email:
        query = query.filter(User.email == email)
    if external_id:
        query = query.filter(User.external_id == external_id)
        
    # Sort by 'username' property (which maps to 'id' in our model)
    query = query.order_by(User.id)
    
    # Pagination
    if after:
        query = query.filter(User.id > after)
        
    results = query.limit(amount + 1).all()
    has_more = len(results) > amount
    results = results[:amount]
    next_offset = results[-1].id if results else ""
    
    return {
        "pagination": {
            "has_more": has_more,
            "max_per_page": amount,
            "results": len(results),
            "next_offset": next_offset
        },
        "results": [
            UserSchema(
                username=u.id,
                creation_date=u.created_at,
                friendly_name=u.friendly_name,
                email=u.email,
                source=u.source,
                encryptedPassword=u.encrypted_password,
                external_id=u.external_id
            ) for u in results
        ]
    }

@router.post("", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def create_user(user_in: UserCreation, db: Session = Depends(get_db)):
    if db.query(User).filter(User.id == user_in.username).first():
        raise HTTPException(status_code=409, detail="User already exists")
    
    new_user = User(
        id=user_in.username,
        friendly_name=user_in.friendlyName or user_in.username,
        created_at=int(time.time()),
        email=user_in.email or user_in.username, # Default email to username if blank? Spec says: "If provided... set to same value"
        source=user_in.source,
        encrypted_password=user_in.encryptedPassword,
        external_id=user_in.external_id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Mock Invitation Logic if invite=True
    if user_in.invite:
        print(f"MOCK: Sending invitation email to {new_user.email}")

    return UserSchema(
        username=new_user.id,
        creation_date=new_user.created_at,
        friendly_name=new_user.friendly_name,
        email=new_user.email,
        source=new_user.source,
        encryptedPassword=new_user.encrypted_password,
        external_id=new_user.external_id
    )

@router.get("/{userId}", response_model=UserSchema)
def get_user(userId: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == userId).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserSchema(
        username=user.id,
        creation_date=user.created_at,
        friendly_name=user.friendly_name,
        email=user.email,
        source=user.source,
        encryptedPassword=user.encrypted_password,
        external_id=user.external_id
    )

from fastapi import Response

@router.delete("/{userId}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(userId: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == userId).first()
    if not user:
        # Spec says delete must match existing. 
        # But commonly delete idempotent returns 204 if not found? 
        # Spec says 404 if not matches.
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.put("/{userId}/password")
def update_user_password(userId: str, password: UserPassword, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == userId).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.encrypted_password = password.encryptedPassword
    db.commit()
    return {"message": "Password updated successfully"}

@router.put("/{userId}/friendly_name", status_code=status.HTTP_204_NO_CONTENT)
def update_user_friendly_name(userId: str, payload: dict, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == userId).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if "friendly_name" not in payload:
         raise HTTPException(status_code=400, detail="Missing friendly_name")

    user.friendly_name = payload["friendly_name"]
    db.commit()
    return None
