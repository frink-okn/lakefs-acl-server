import pytest
import sys
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# FORCE SQLite for testing BEFORE importing database module
os.environ["DATABASE_CONNECTION_STRING"] = "sqlite:///:memory:"

# Add acl_server to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../acl_server')))

from database import Base, get_db
from main import app
import security

# Setup In-Memory SQLite for Tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """
    Creates a fresh database session for a test.
    Rolls back transaction after test completes.
    """
    Base.metadata.create_all(bind=engine)
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(db_session):
    """
    FastAPI TestClient with overridden DB dependency.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    # Mock Token Verification for most tests, or use valid token
    # For unit tests, we might want to bypass auth or use a valid token
    
    yield TestClient(app)
    
    del app.dependency_overrides[get_db]

@pytest.fixture(scope="session")
def valid_token():
    return security.API_TOKEN

@pytest.fixture(scope="session")
def auth_headers(valid_token):
    return {"Authorization": f"Bearer {valid_token}"}
