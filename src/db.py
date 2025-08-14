import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, DeclarativeBase
from dotenv import load_dotenv

load_dotenv()

# Get DATABASE_URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")
print(f"DEBUG: DATABASE_URL from environment: {DATABASE_URL}")

# Only create engine if DATABASE_URL is available
if DATABASE_URL:
    try:
        # Configure engine with serverless-friendly settings
        engine = create_engine(
            DATABASE_URL, 
            pool_pre_ping=True, 
            future=True,
            # Serverless-friendly pool settings
            pool_size=1,
            max_overflow=0,
            pool_recycle=300,
            pool_timeout=20
        )
        SessionLocal = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True))
        print("DEBUG: Database engine created successfully")
    except Exception as e:
        print(f"DEBUG: Failed to create database engine: {e}")
        engine = None
        SessionLocal = None
else:
    # Create a dummy engine for serverless environments without database
    engine = None
    SessionLocal = None
    print("DEBUG: No DATABASE_URL provided, skipping database setup")


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