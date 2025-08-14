import os
import re
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, DeclarativeBase
from dotenv import load_dotenv

load_dotenv()

def convert_psql_to_sqlalchemy(psql_url):
    """Convert psql connection string to SQLAlchemy format"""
    # Remove 'psql' prefix if present
    if psql_url.startswith('psql '):
        psql_url = psql_url[5:]
    
    # Remove any surrounding quotes
    psql_url = psql_url.strip('"\'')
    
    # Convert postgres:// to postgresql+pg8000://
    if psql_url.startswith('postgres://'):
        sqlalchemy_url = psql_url.replace('postgres://', 'postgresql+pg8000://', 1)
    elif psql_url.startswith('postgresql://'):
        sqlalchemy_url = psql_url.replace('postgresql://', 'postgresql+pg8000://', 1)
    else:
        sqlalchemy_url = psql_url
    
    return sqlalchemy_url

# Get DATABASE_URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

# Convert psql format to SQLAlchemy format if needed
if DATABASE_URL and DATABASE_URL.startswith('psql '):
    DATABASE_URL = convert_psql_to_sqlalchemy(DATABASE_URL)

# Only create engine if DATABASE_URL is available
if DATABASE_URL:
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
else:
    # Create a dummy engine for serverless environments without database
    engine = None
    SessionLocal = None


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