from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from database import engine, Base
import models
from routers import users, groups, policies, credentials
from schemas import VersionConfig
import security

# Create tables
Base.metadata.create_all(bind=engine)

from init_db import init_db_data
from database import SessionLocal

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize DB
    db = SessionLocal()
    try:
        init_db_data(db)
    finally:
        db.close()
    yield
    # Shutdown logic (if any) goes here

app = FastAPI(
    title="LakeFS ACL Server",
    description="Python implementation of LakeFS Auth API",
    version="0.1.0",
    lifespan=lifespan
)

# Prefix all auth routes with /api/v1
API_PREFIX = "/api/v1"

# Protect Data/Auth Routes
auth_deps = [Depends(security.verify_api_token)]

app.include_router(users.router, prefix=API_PREFIX, dependencies=auth_deps)
app.include_router(groups.router, prefix=API_PREFIX, dependencies=auth_deps)
app.include_router(policies.router, prefix=API_PREFIX, dependencies=auth_deps)
app.include_router(credentials.router, prefix=API_PREFIX, dependencies=auth_deps)

@app.get(f"{API_PREFIX}/healthcheck", tags=["healthCheck"], status_code=204)
def healthcheck():
    return None

@app.get(f"{API_PREFIX}/config/version", tags=["config"], response_model=VersionConfig)
def get_version():
    return {"version": "0.1.0"}
