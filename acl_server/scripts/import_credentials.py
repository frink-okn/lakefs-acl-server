
import yaml
import sys
import os
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import User, AccessKey, Group, Policy
# Ensure models are loaded
import models 
import security

def import_credentials(yaml_path: str):
    """
    Imports users and credentials from a YAML file.
    Expected YAML format:
    users:
      - id: "username"
        friendly_name: "My Name"
        groups: ["Admins", "Readers"]
        access_keys:
          - access_key_id: "AKIA..."
            secret_access_key: "secret..."
    """
    
    if not os.path.exists(yaml_path):
        print(f"File not found: {yaml_path}")
        return

    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)

    db = SessionLocal()
    try:
        # Pre-create standard groups if missing
        standard_groups = ["Admins", "Startups", "Viewers", "Developers"]
        for g_name in standard_groups:
            if not db.query(Group).filter(Group.id == g_name).first():
                # For simplicity, using name as ID
                grp = Group(id=g_name, description=f"Standard {g_name} group")
                db.add(grp)
        db.commit()

        count = 0
        for user_data in data.get('users', []):
            user_id = user_data['id']
            print(f"Processing user: {user_id}")
            
            # Find or Create User
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                user = User(
                    id=user_id,
                    friendly_name=user_data.get('friendly_name'),
                    email=user_data.get('email')
                )
                db.add(user)
            
            # Add Groups
            for group_id in user_data.get('groups', []):
                group = db.query(Group).filter(Group.id == group_id).first()
                if group and group not in user.groups:
                    user.groups.append(group)
            
            # Add Credentials
            for cred in user_data.get('access_keys', []):
                ak = cred['access_key_id']
                sk = cred['secret_access_key']
                
                existing = db.query(AccessKey).filter(AccessKey.access_access_key_id == ak).first()
                if not existing:
                    # Encrypt before storing
                    encrypted_sk = security.encrypt_secret(sk)
                    
                    new_key = AccessKey(
                        access_access_key_id=ak,
                        access_secret_access_key=encrypted_sk,
                        user_id=user_id
                    )
                    db.add(new_key)
            
            count += 1
        
        db.commit()
        print(f"Successfully imported {count} users.")
        
    except Exception as e:
        print(f"Error importing: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python import_credentials.py <path_to_yaml>")
        sys.exit(1)
    
    import_credentials(sys.argv[1])
