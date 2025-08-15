import os
import sys
from http.server import BaseHTTPRequestHandler
import json

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import User, Lesson, Problem, ProblemOption
from sqlalchemy import select, create_engine
from sqlalchemy.orm import sessionmaker, Session

def create_db_session():
    """Create a database session using the environment variable"""
    database_url = os.getenv("POSTGRES_URL_NON_POOLING") or os.getenv("DATABASE_URL")
    if not database_url:
        return None
    
    # Convert postgres:// to postgresql:// if needed
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    engine = create_engine(database_url, connect_args={"sslmode": "require"})
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()

def ensure_demo_user(db: Session):
    user = db.get(User, 1)
    if not user:
        user = User(id=1, username="demo", total_xp=0, current_streak=0, best_streak=0)
        db.add(user)
    return user

def create_lessons(db: Session):
    if db.scalar(select(Lesson).limit(1)):
        return "Lessons already exist"

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
    
    return "Lessons created successfully"

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            db = create_db_session()
            if db is None:
                self.send_response(503)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'error': 'DatabaseError', 
                    'message': 'DATABASE_URL not configured',
                    'debug': f"DATABASE_URL: {os.getenv('DATABASE_URL')}"
                }).encode())
                return

            try:
                ensure_demo_user(db)
                result = create_lessons(db)
                db.commit()
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'status': 'success',
                    'message': 'Seed complete',
                    'result': result
                }).encode())
                
            except Exception as e:
                db.rollback()
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'error': 'SeedError',
                    'message': str(e)
                }).encode())
            finally:
                db.close()
                
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'error': 'InternalError',
                'message': str(e)
            }).encode())
