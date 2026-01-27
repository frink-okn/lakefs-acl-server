
import pytest
from logic import get_effective_policies
from models import User, Group, Policy

def test_effective_policies():
    """Verify policy aggregation logic"""
    # Create Policies
    p1 = Policy(id="p1", statement=[{"effect": "allow"}])
    p2 = Policy(id="p2", statement=[{"effect": "deny"}])
    p3 = Policy(id="p3", statement=[{"effect": "allow"}])
    
    # Create Groups
    g1 = Group(id="g1", policies=[p2])
    
    # Create User with Direct Policy and Group Membership
    user = User(
        id="u1",
        policies=[p1],
        groups=[g1] # Inherits p2 from g1
    )
    
    effective = get_effective_policies(user)
    
    # User should have p1 (direct) and p2 (inherited)
    policy_ids = {p.id for p in effective}
    assert "p1" in policy_ids
    assert "p2" in policy_ids
    assert "p3" not in policy_ids
    assert len(effective) == 2

def test_policy_deduplication():
    """Verify logic does not duplicate policies"""
    p1 = Policy(id="p1")
    g1 = Group(id="g1", policies=[p1])
    
    # User has p1 directly AND via group g1
    user = User(
        id="u1",
        policies=[p1],
        groups=[g1]
    )
    
    effective = get_effective_policies(user)
    assert len(effective) == 1
    assert effective[0].id == "p1"
