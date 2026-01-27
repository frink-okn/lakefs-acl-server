
from typing import List
from models import User, Policy

def get_effective_policies(user: User) -> List[Policy]:
    """
    Returns all policies for a user, including:
    1. Policies attached directly to the user.
    2. Policies attached to any group the user is a member of.
    """
    policies = {} # Dedup by ID
    
    # 1. Direct Policies
    for p in user.policies:
        policies[p.id] = p
        
    # 2. Group Policies
    for group in user.groups:
        for p in group.policies:
            policies[p.id] = p
            
    return list(policies.values())
