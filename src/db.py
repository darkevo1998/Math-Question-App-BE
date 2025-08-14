import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, DeclarativeBase
from dotenv import load_dotenv

load_dotenv()

# Use DATABASE_URL from environment, with a fallback for local development
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+pg8000://postgres:admin1234@localhost:5432/mathquest")

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


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
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