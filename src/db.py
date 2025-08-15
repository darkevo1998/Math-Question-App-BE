import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, DeclarativeBase
from dotenv import load_dotenv

load_dotenv()

# Get DATABASE_URL from environment - prefer non-pooling for serverless
POSTGRES_URL_NON_POOLING = os.getenv("POSTGRES_URL_NON_POOLING")
DATABASE_URL_ENV = os.getenv("DATABASE_URL")
print(f"DEBUG: POSTGRES_URL_NON_POOLING: {POSTGRES_URL_NON_POOLING}")
print(f"DEBUG: DATABASE_URL from env: {DATABASE_URL_ENV}")

DATABASE_URL = POSTGRES_URL_NON_POOLING or DATABASE_URL_ENV
print(f"DEBUG: Final DATABASE_URL selected: {DATABASE_URL}")

# Store the original URL for use in other modules
ORIGINAL_DATABASE_URL = DATABASE_URL

# Only create engine if DATABASE_URL is available
if DATABASE_URL:
    try:
        # Fix postgres:// to postgresql:// for SQLAlchemy compatibility
        if DATABASE_URL.startswith('postgres://'):
            DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
            print(f"DEBUG: Fixed DATABASE_URL to: {DATABASE_URL}")
        
        print(f"DEBUG: Attempting to create engine with URL: {DATABASE_URL}")
        
        # Configure engine with more robust settings for Supabase
        print(f"DEBUG: Creating engine with URL: {DATABASE_URL}")
        
        # Use auto-detection since that's what works
        engine = create_engine(
            DATABASE_URL, 
            pool_pre_ping=True, 
            future=True,
            # Serverless-friendly pool settings
            pool_size=1,
            max_overflow=0,
            pool_recycle=300,
            pool_timeout=30,
            # More flexible SSL settings for pg8000
            connect_args={
                "application_name": "math-question-app"
            }
        )
        print("DEBUG: Engine created successfully with auto-detection")
        SessionLocal = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True))
        print("DEBUG: Database engine created successfully")
        
        # Test the connection immediately
        try:
            from sqlalchemy import text
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                print("DEBUG: Database connection test successful")
        except Exception as conn_e:
            print(f"DEBUG: Database connection test failed: {conn_e}")
            # Don't raise the exception, just log it and continue
            print(f"DEBUG: Connection test failed but continuing: {conn_e}")
            # The engine is still created, just the test failed
            
    except Exception as e:
        print(f"DEBUG: Failed to create database engine: {e}")
        print(f"DEBUG: Exception type: {type(e)}")
        import traceback
        print(f"DEBUG: Full traceback: {traceback.format_exc()}")
        engine = None
        SessionLocal = None
        print("DEBUG: Engine and SessionLocal set to None due to exception")
else:
    # Create a dummy engine for serverless environments without database
    engine = None
    SessionLocal = None
    print("DEBUG: No DATABASE_URL provided, skipping database setup")

# Final debug output
print(f"DEBUG: Final engine state: {engine is not None}")
print(f"DEBUG: Final SessionLocal state: {SessionLocal is not None}")


class Base(DeclarativeBase):
    pass


def get_db():
    if SessionLocal is None:
        raise Exception("Database not configured")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    # Only try to connect if we have a valid engine
    if engine is None:
        print("Database not configured, skipping initialization")
        return
        
    # Only try to connect if we're not in a serverless environment
    if os.getenv("VERCEL"):
        print("Skipping database initialization in serverless environment")
        return
        
    # migrations handle schema; this ensures connection is valid
    try:
        with engine.connect() as conn:
            pass
    except Exception as e:
        print(f"Database connection failed: {e}")
        # Don't raise the exception in serverless environments
        if not os.getenv("VERCEL"):
            raise 