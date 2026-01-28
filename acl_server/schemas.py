
from pydantic import BaseModel, Field, AliasChoices
from typing import List, Optional, Any, Dict

# --- Common ---
class Pagination(BaseModel):
    has_more: bool
    next_offset: str
    results: int
    max_per_page: int

class Error(BaseModel):
    message: str

class VersionConfig(BaseModel):
    version: str

# --- Users ---
class User(BaseModel):
    username: str = Field(..., description="A unique identifier for the user.") # This is the ID
    creation_date: int = Field(..., description="Unix Epoch in seconds.")
    friendly_name: Optional[str] = None
    email: Optional[str] = None
    source: Optional[str] = None
    encryptedPassword: Optional[str] = None
    external_id: Optional[str] = None

class UserCreation(BaseModel):
    username: str = Field(..., min_length=1)
    email: Optional[str] = None
    friendlyName: Optional[str] = None
    source: Optional[str] = None
    encryptedPassword: Optional[str] = None
    external_id: Optional[str] = None
    invite: Optional[bool] = False

class UserList(BaseModel):
    pagination: Pagination
    results: List[User]

class UserPassword(BaseModel):
    encryptedPassword: str

# --- Groups ---
class Group(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    creation_date: int

class GroupCreation(BaseModel):
    id: str
    description: Optional[str] = None

class GroupList(BaseModel):
    pagination: Pagination
    results: List[Group]

# --- Policies ---
from pydantic import RootModel

class PolicyCondition(RootModel):
    root: Dict[str, List[str]]

class Statement(BaseModel):
    effect: str
    resource: str
    action: List[str]
    condition: Optional[Dict[str, Any]] = None

class Policy(BaseModel):
    name: str # The ID
    creation_date: Optional[int] = None
    statement: List[Statement]
    acl: Optional[str] = None

class PolicyList(BaseModel):
    pagination: Pagination
    results: List[Policy]

# --- Credentials ---
class Credentials(BaseModel):
    access_key_id: str
    creation_date: int

class CredentialsCreation(BaseModel):
    access_key_id: Optional[str] = None
    secret_access_key: Optional[str] = None

class CredentialsList(BaseModel):
    pagination: Pagination
    results: List[Credentials]

class CredentialsWithSecret(BaseModel):
    access_key_id: str
    secret_access_key: str
    creation_date: int
    user_id: Optional[int] = None # Deprecated, must be int
    user_name: Optional[str] = None
