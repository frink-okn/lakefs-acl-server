
from sqlalchemy.orm import Session
from models import Group, Policy, User
import time
import json
from typing import List, Dict

# --- Definitions ---
POLICIES_DATA = [
    {
        "id": "FSFullAccess",
        "statement": [{"action": ["fs:*"], "effect": "allow", "resource": "*"}]
    },
    {
        "id": "FSReadAll",
        "statement": [{"action": ["fs:List*", "fs:Read*"], "effect": "allow", "resource": "*"}]
    },
    {
        "id": "FSReadWriteAll",
        "statement": [{
            "action": [
                "fs:Read*", "fs:List*", "fs:WriteObject", "fs:DeleteObject", 
                "fs:RevertBranch", "fs:CreateBranch", "fs:CreateTag", 
                "fs:DeleteBranch", "fs:DeleteTag", "fs:CreateCommit"
            ],
            "effect": "allow",
            "resource": "*"
        }]
    },
    {
        "id": "AuthFullAccess",
        "statement": [{"action": ["auth:*"], "effect": "allow", "resource": "*"}]
    },
    {
        "id": "AuthManageOwnCredentials",
        "statement": [{
            "action": [
                "auth:CreateCredentials", "auth:DeleteCredentials", 
                "auth:ListCredentials", "auth:ReadCredentials"
            ],
            "effect": "allow",
            "resource": "arn:lakefs:auth:::user/${user}"
        }]
    },
    {
        "id": "RepoManagementFullAccess",
        "statement": [
            {"action": ["ci:*"], "effect": "allow", "resource": "*"},
            {"action": ["retention:*"], "effect": "allow", "resource": "*"}
        ]
    },
    {
        "id": "RepoManagementReadAll",
        "statement": [
            {"action": ["ci:Read*"], "effect": "allow", "resource": "*"},
            {"action": ["retention:Get*"], "effect": "allow", "resource": "*"}
        ]
    }
]

GROUPS_DATA = {
    "Admins": ["FSFullAccess", "AuthFullAccess", "RepoManagementFullAccess"],
    "SuperUsers": ["FSFullAccess", "AuthManageOwnCredentials"],
    "Developers": ["FSReadWriteAll", "AuthManageOwnCredentials", "RepoManagementReadAll"],
    "Viewers": ["FSReadAll", "AuthManageOwnCredentials"]
}

def init_db_data(db: Session):
    print("Initializing Database Data...")
    
    # 1. Create Policies
    for p_data in POLICIES_DATA:
        policy_id = p_data["id"] # name in schema, id in model
        existing = db.query(Policy).filter(Policy.id == policy_id).first()
        if not existing:
            print(f"Creating Policy: {policy_id}")
            new_policy = Policy(
                id=policy_id,
                statement=p_data["statement"],
                created_at=int(time.time()),
                acl="public" # Optional default
            )
            db.add(new_policy)
        else:
            print(f"Policy {policy_id} already exists.")
    
    db.commit()

    # 2. Create Groups & Attach Policies
    for group_id, policies in GROUPS_DATA.items():
        group = db.query(Group).filter(Group.id == group_id).first()
        if not group:
            print(f"Creating Group: {group_id}")
            group = Group(
                id=group_id, 
                description=f"Standard {group_id} group", 
                created_at=int(time.time())
            )
            db.add(group)
            db.commit() # Commit to get ID reference if needed (though UUID string here)
            db.refresh(group)
        else:
            print(f"Group {group_id} already exists.")
        
        # Attach Policies
        current_policies = {p.id for p in group.policies}
        for p_id in policies:
            if p_id not in current_policies:
                policy = db.query(Policy).filter(Policy.id == p_id).first()
                if policy:
                    print(f"Attaching {p_id} to {group_id}")
                    group.policies.append(policy)
        
        db.commit()
    
    print("Initialization Complete.")
