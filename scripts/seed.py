import os
import sys
from sqlalchemy import select
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db import engine, SessionLocal
from src.models import User, Lesson, Problem, ProblemOption

load_dotenv()


def ensure_demo_user(db: Session):
    user = db.get(User, 1)
    if not user:
        user = User(id=1, username="demo", total_xp=0, current_streak=0, best_streak=0)
        db.add(user)
    return user


def create_lessons(db: Session):
    if db.scalar(select(Lesson).limit(1)):
        return

    lessons = [
        ("Basic Arithmetic", "Addition and subtraction warm-up", 1),
        ("Multiplication Mastery", "Times tables practice", 2),
        ("Division Basics", "Simple division problems", 3),
    ]
    for title, desc, order_idx in lessons:
        db.add(Lesson(title=title, description=desc, order_index=order_idx))
    db.flush()

    # Fetch lessons back with IDs
    basic = db.execute(select(Lesson).where(Lesson.title == "Basic Arithmetic")).scalar_one()
    mult = db.execute(select(Lesson).where(Lesson.title == "Multiplication Mastery")).scalar_one()
    divv = db.execute(select(Lesson).where(Lesson.title == "Division Basics")).scalar_one()

    # Basic Arithmetic (3 problems)
    p1 = Problem(lesson_id=basic.id, type="mcq", prompt="What is 2 + 3?")
    p2 = Problem(lesson_id=basic.id, type="input", prompt="What is 10 - 4?", correct_answer_text="6")
    p3 = Problem(lesson_id=basic.id, type="mcq", prompt="What is 7 + 1?")
    db.add_all([p1, p2, p3])
    db.flush()
    db.add_all([
        ProblemOption(problem_id=p1.id, text="4", is_correct=False),
        ProblemOption(problem_id=p1.id, text="5", is_correct=True),
        ProblemOption(problem_id=p1.id, text="6", is_correct=False),
        ProblemOption(problem_id=p3.id, text="9", is_correct=False),
        ProblemOption(problem_id=p3.id, text="8", is_correct=True),
        ProblemOption(problem_id=p3.id, text="7", is_correct=False),
    ])

    # Multiplication (3 problems)
    m1 = Problem(lesson_id=mult.id, type="input", prompt="What is 3 x 4?", correct_answer_text="12")
    m2 = Problem(lesson_id=mult.id, type="mcq", prompt="What is 5 x 5?")
    m3 = Problem(lesson_id=mult.id, type="input", prompt="What is 6 x 2?", correct_answer_text="12")
    db.add_all([m1, m2, m3])
    db.flush()
    db.add_all([
        ProblemOption(problem_id=m2.id, text="10", is_correct=False),
        ProblemOption(problem_id=m2.id, text="20", is_correct=False),
        ProblemOption(problem_id=m2.id, text="25", is_correct=True),
    ])

    # Division (3 problems)
    d1 = Problem(lesson_id=divv.id, type="mcq", prompt="What is 8 ÷ 2?")
    d2 = Problem(lesson_id=divv.id, type="input", prompt="What is 9 ÷ 3?", correct_answer_text="3")
    d3 = Problem(lesson_id=divv.id, type="mcq", prompt="What is 12 ÷ 4?")
    db.add_all([d1, d2, d3])
    db.flush()
    db.add_all([
        ProblemOption(problem_id=d1.id, text="4", is_correct=True),
        ProblemOption(problem_id=d1.id, text="2", is_correct=False),
        ProblemOption(problem_id=d3.id, text="2", is_correct=False),
        ProblemOption(problem_id=d3.id, text="3", is_correct=True),
    ])


def main():
    db = SessionLocal()
    try:
        ensure_demo_user(db)
        create_lessons(db)
        db.commit()
        print("Seed complete.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main() 