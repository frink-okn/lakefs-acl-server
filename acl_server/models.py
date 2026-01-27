
from sqlalchemy import Column, String, Integer, BigInteger, ForeignKey, Table, Text, JSON
from sqlalchemy.orm import relationship
from database import Base
import time

# Association Tables
user_groups = Table('auth_user_groups', Base.metadata,
    Column('user_id', String, ForeignKey('auth_users.id'), primary_key=True),
    Column('group_id', String, ForeignKey('auth_groups.id'), primary_key=True),
    Column('created_at', BigInteger, default=lambda: int(time.time()))
)

group_policies = Table('auth_group_policies', Base.metadata,
    Column('group_id', String, ForeignKey('auth_groups.id'), primary_key=True),
    Column('policy_id', String, ForeignKey('auth_policies.id'), primary_key=True),
    Column('created_at', BigInteger, default=lambda: int(time.time()))
)

user_policies = Table('auth_user_policies', Base.metadata,
    Column('user_id', String, ForeignKey('auth_users.id'), primary_key=True),
    Column('policy_id', String, ForeignKey('auth_policies.id'), primary_key=True),
    Column('created_at', BigInteger, default=lambda: int(time.time()))
)

class User(Base):
    __tablename__ = "auth_users"
    id = Column(String, primary_key=True, index=True) # This is the Username
    friendly_name = Column(String, nullable=True)
    created_at = Column(BigInteger, default=lambda: int(time.time()))
    email = Column(String, nullable=True)
    source = Column(String, nullable=True)
    encrypted_password = Column(String, nullable=True) # Stored as binary/string
    external_id = Column(String, nullable=True)
    
    # Relationships
    access_keys = relationship("AccessKey", back_populates="user")
    groups = relationship("Group", secondary=user_groups, back_populates="users")
    policies = relationship("Policy", secondary=user_policies, back_populates="users")

class Group(Base):
    __tablename__ = "auth_groups"
    id = Column(String, primary_key=True, index=True)
    description = Column(String, nullable=True)
    created_at = Column(BigInteger, default=lambda: int(time.time()))
    
    users = relationship("User", secondary=user_groups, back_populates="groups")
    policies = relationship("Policy", secondary=group_policies, back_populates="groups")

class Policy(Base):
    __tablename__ = "auth_policies"
    id = Column(String, primary_key=True, index=True)
    description = Column(String, nullable=True)
    created_at = Column(BigInteger, default=lambda: int(time.time()))
    statement = Column(JSON) # Stores the policy JSON
    acl = Column(String, nullable=True)
    
    groups = relationship("Group", secondary=group_policies, back_populates="policies")
    users = relationship("User", secondary=user_policies, back_populates="policies")

class AccessKey(Base):
    __tablename__ = "auth_credentials"
    access_access_key_id = Column(String, primary_key=True)
    access_secret_access_key = Column(String) # Encrypted?
    user_id = Column(String, ForeignKey("auth_users.id"))
    created_at = Column(BigInteger, default=lambda: int(time.time()))
    
    user = relationship("User", back_populates="access_keys")
