import os
import sys
import time
from sqlalchemy import create_engine, text
from urllib.parse import urlparse

# Add current dir to path to allow imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_database_if_not_exists(url):
    """
    Parses the URL, connects to the 'postgres' database, and creates the target database if it doesn't exist.
    """
    if not url.startswith("postgresql"):
        print(f"Skipping DB creation for non-postgres URL: {url.split(':')[0]}...")
        return

    # Parse the URL
    # format: postgresql://user:pass@host:port/dbname?options
    try:
        # We need to construct a URL for the 'postgres' default database
        # This is a bit hacky with string replacement but valid for standard SQLAlchmey URLs
        if "/postgres" in url:
             # Already pointing to postgres or default, nothing to create
             return
        
        # Split the URL to isolate the database name
        # Assumption: Last part after / is the DB name (ignoring query params)
        base_url, db_name_part = url.rsplit('/', 1)
        if '?' in db_name_part:
            db_name = db_name_part.split('?')[0]
        else:
            db_name = db_name_part

        # Verify db_name isn't empty
        if not db_name:
            print("Could not parse database name.")
            return

        postgres_url = f"{base_url}/postgres"
        
        print(f"Checking if database '{db_name}' exists...")
        # Connect to 'postgres' system db
        engine = create_engine(postgres_url, isolation_level="AUTOCOMMIT")
        
        with engine.connect() as conn:
            # Check if DB exists
            # Use text() for raw SQL
            result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'"))
            if not result.scalar():
                print(f"Database '{db_name}' does not exist. Creating...")
                conn.execute(text(f"CREATE DATABASE {db_name}"))
                print(f"Database '{db_name}' created successfully.")
            else:
                print(f"Database '{db_name}' already exists.")
                
    except Exception as e:
        print(f"Warning: Failed to ensure database exists. Error: {e}")
        print("Proceeding with initialization (assuming DB exists or creation handled elsewhere)...")

if __name__ == "__main__":
    db_url = os.getenv("DATABASE_CONNECTION_STRING")
    if not db_url:
        print("DATABASE_CONNECTION_STRING is not set.")
        sys.exit(1)

    # 1. Ensure DB Exists (Postgres only)
    create_database_if_not_exists(db_url)

    # 2. Initialize Tables and Data
    # Import here to avoid early engine bindings failing if DB didn't exist
    try:
        from database import engine, Base, SessionLocal
        from init_db import init_db_data
        
        print("Creating tables...")
        Base.metadata.create_all(bind=engine)
        
        print("Initializing data...")
        db = SessionLocal()
        try:
            init_db_data(db)
        finally:
            db.close()
            
        print("Database initialization completed successfully.")
        
    except Exception as e:
        print(f"Initialization Failed: {e}")
        sys.exit(1)
