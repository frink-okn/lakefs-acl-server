
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from database import get_db
from models import Group, User, Policy
from schemas import Policy as PolicySchema, PolicyList, Pagination
from typing import List, Optional
import time

# We might need logic for effective policies
# from logic import get_effective_policies 
# Let's reimplement simple effective policy logic here or import it if compatible

router = APIRouter(prefix="/auth", tags=["auth"])

# --- Policy CRUD ---

@router.get("/policies", response_model=PolicyList)
def list_policies(
    prefix: str = "",
    after: str = "",
    amount: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(Policy)
    if prefix:
        query = query.filter(Policy.id.startswith(prefix))
    
    query = query.order_by(Policy.id)
    
    if after:
        query = query.filter(Policy.id > after)
        
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
            PolicySchema(
                name=p.id,
                creation_date=p.created_at,
                statement=p.statement or [],
                acl=p.acl
            ) for p in results
        ]
    }

@router.post("/policies", response_model=PolicySchema, status_code=status.HTTP_201_CREATED)
def create_policy(policy_in: PolicySchema, db: Session = Depends(get_db)):
    # ID is the name
    if db.query(Policy).filter(Policy.id == policy_in.name).first():
         raise HTTPException(status_code=409, detail="Policy already exists")
         
    new_policy = Policy(
        id=policy_in.name,
        created_at=int(time.time()),
        statement=[s.dict() for s in policy_in.statement], # Store list of dicts
        acl=policy_in.acl
    )
    db.add(new_policy)
    db.commit()
    db.refresh(new_policy)
    
    return PolicySchema(
        name=new_policy.id,
        creation_date=new_policy.created_at,
        statement=new_policy.statement,
        acl=new_policy.acl
    )

@router.get("/policies/{policyId}", response_model=PolicySchema)
def get_policy(policyId: str, db: Session = Depends(get_db)):
    policy = db.query(Policy).filter(Policy.id == policyId).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    return PolicySchema(
        name=policy.id,
        creation_date=policy.created_at,
        statement=policy.statement,
        acl=policy.acl
    )

@router.put("/policies/{policyId}", response_model=PolicySchema)
def update_policy(policyId: str, policy_in: PolicySchema, db: Session = Depends(get_db)):
    policy = db.query(Policy).filter(Policy.id == policyId).first()
    if not policy:
         # Spec says update existing, if sends new ID (name) it might mean rename?
         # Usually Put on ID implies update content.
         raise HTTPException(status_code=404, detail="Policy not found")
    
    policy.statement = [s.dict() for s in policy_in.statement]
    policy.acl = policy_in.acl
    # policy.description? Schema doesn't have description for input? 
    # Actually Policy Schema has no description in spec.
    
    db.commit()
    db.refresh(policy)
    
    return PolicySchema(
        name=policy.id,
        creation_date=policy.created_at,
        statement=policy.statement,
        acl=policy.acl
    )

from fastapi import Response

@router.delete("/policies/{policyId}", status_code=status.HTTP_204_NO_CONTENT)
def delete_policy(policyId: str, db: Session = Depends(get_db)):
    policy = db.query(Policy).filter(Policy.id == policyId).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
        
    db.delete(policy)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# --- User Policies ---

@router.get("/users/{userId}/policies", response_model=PolicyList)
def list_user_policies(
    userId: str, 
    effective: bool = False,
    prefix: str = "",
    after: str = "",
    amount: int = 100,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == userId).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if effective:
        # Collect distinct policies from user + all groups
        policies = set(user.policies)
        for group in user.groups:
            policies.update(group.policies)
        policies = sorted(list(policies), key=lambda p: p.id)
    else:
        policies = sorted(user.policies, key=lambda p: p.id)
        
    if prefix:
        policies = [p for p in policies if p.id.startswith(prefix)]
    if after:
        policies = [p for p in policies if p.id > after]
        
    has_more = len(policies) > amount
    policies = policies[:amount]
    next_offset = policies[-1].id if policies else ""
    
    return {
        "pagination": {
            "has_more": has_more,
            "max_per_page": amount,
            "results": len(policies),
            "next_offset": next_offset
        },
        "results": [
             PolicySchema(
                name=p.id,
                creation_date=p.created_at,
                statement=p.statement or [],
                acl=p.acl
            ) for p in policies
        ]
    }

@router.put("/users/{userId}/policies/{policyId}", status_code=status.HTTP_201_CREATED)
def attach_policy_to_user(userId: str, policyId: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == userId).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    policy = db.query(Policy).filter(Policy.id == policyId).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
        
    if policy not in user.policies:
        user.policies.append(policy)
        db.commit()
    
    return None

@router.delete("/users/{userId}/policies/{policyId}", status_code=status.HTTP_204_NO_CONTENT)
def detach_policy_from_user(userId: str, policyId: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == userId).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    policy = db.query(Policy).filter(Policy.id == policyId).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
        
    if policy in user.policies:
        user.policies.remove(policy)
        db.commit()
        
    return Response(status_code=status.HTTP_204_NO_CONTENT)
