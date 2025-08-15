import os
import tempfile
import pytest
from sqlalchemy.orm import Session

# Set test database URL BEFORE importing app/db
TEST_DB = os.path.join(tempfile.gettempdir(), "mathquest_test.db")
os.environ["DATABASE_URL"] = f"postgresql+pg8000://postgres:admin1234@localhost:5432/mathquest_test"

from src.db import Base, engine, SessionLocal  # noqa: E402
from app import create_app  # noqa: E402
from src.models import User, Lesson, Problem, ProblemOption  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    # Drop and recreate test database
    from sqlalchemy import text
    with engine.connect() as conn:
        conn.execute(text("DROP DATABASE IF EXISTS mathquest_test"))
        conn.execute(text("CREATE DATABASE mathquest_test"))
    Base.metadata.create_all(bind=engine)
    yield
    # Cleanup
    with engine.connect() as conn:
        conn.execute(text("DROP DATABASE IF EXISTS mathquest_test"))


@pytest.fixture()
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client(db_session: Session):
    # seed basic data for API tests
    if not db_session.get(User, 1):
        db_session.add(User(id=1, username="demo"))
    lesson = Lesson(title="Test Lesson", description="Test", order_index=1)
    db_session.add(lesson)
    db_session.flush()
    # problems
    p1 = Problem(lesson_id=lesson.id, type="mcq", prompt="2+2=?")
    p2 = Problem(lesson_id=lesson.id, type="input", prompt="3x4?", correct_answer_text="12")
    db_session.add_all([p1, p2])
    db_session.flush()
    db_session.add_all([
        ProblemOption(problem_id=p1.id, text="3", is_correct=False),
        ProblemOption(problem_id=p1.id, text="4", is_correct=True),
        ProblemOption(problem_id=p1.id, text="5", is_correct=False),
    ])
    db_session.commit()

    app = create_app()
    with app.test_client() as c:
        yield c 