from flask import request, jsonify
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, OperationalError
from .db import SessionLocal
from .services.lessons import get_lessons_with_progress, get_lesson_detail
from .services.submit import process_submission, DuplicateAttemptError, ValidationError, InvalidProblemError

DEMO_USER_ID = 1

def register_routes(app):
    """Register all API routes"""
    
    @app.route('/api/lessons', methods=['GET'])
    def list_lessons():
        """List all lessons with progress for the demo user"""
        if SessionLocal is None:
            return jsonify({'error': 'DatabaseError', 'message': 'Database not configured'}), 503
            
        try:
            db: Session = SessionLocal()
            try:
                items = get_lessons_with_progress(db, DEMO_USER_ID)
                return jsonify(items)
            finally:
                db.close()
        except OperationalError as e:
            return jsonify({'error': 'DatabaseError', 'message': 'Database connection failed'}), 503
        except Exception as e:
            return jsonify({'error': 'InternalError', 'message': str(e)}), 500

    @app.route('/api/lessons/<int:lesson_id>', methods=['GET'])
    def get_lesson(lesson_id):
        """Get lesson details with problems (correct answers not included)"""
        if SessionLocal is None:
            return jsonify({'error': 'DatabaseError', 'message': 'Database not configured'}), 503
            
        try:
            db: Session = SessionLocal()
            try:
                data = get_lesson_detail(db, DEMO_USER_ID, lesson_id)
                if not data:
                    return jsonify({'error': 'NotFound', 'message': 'Lesson not found'}), 404
                return jsonify(data)
            finally:
                db.close()
        except OperationalError as e:
            return jsonify({'error': 'DatabaseError', 'message': 'Database connection failed'}), 503
        except Exception as e:
            return jsonify({'error': 'InternalError', 'message': str(e)}), 500

    @app.route('/api/lessons/<int:lesson_id>/submit', methods=['POST'])
    def submit_lesson(lesson_id):
        """Submit answers for a lesson (idempotent)"""
        if SessionLocal is None:
            return jsonify({'error': 'DatabaseError', 'message': 'Database not configured'}), 503
            
        try:
            db: Session = SessionLocal()
            try:
                payload = request.get_json(silent=True) or {}
                try:
                    result = process_submission(db, DEMO_USER_ID, lesson_id, payload)
                    db.commit()
                    return jsonify(result)
                except DuplicateAttemptError as e:
                    db.rollback()
                    return jsonify({'error': 'DuplicateAttempt', 'message': str(e)}), 409
                except InvalidProblemError as e:
                    db.rollback()
                    return jsonify({'error': 'InvalidProblem', 'message': str(e)}), 422
                except ValidationError as e:
                    db.rollback()
                    return jsonify({'error': 'Validation', 'message': str(e)}), 400
            except Exception:
                db.rollback()
                raise
            finally:
                db.close()
        except OperationalError as e:
            return jsonify({'error': 'DatabaseError', 'message': 'Database connection failed'}), 503
        except Exception as e:
            return jsonify({'error': 'InternalError', 'message': str(e)}), 500

    @app.route('/api/profile', methods=['GET'])
    def get_profile():
        """Get user profile and statistics"""
        if SessionLocal is None:
            return jsonify({'error': 'DatabaseError', 'message': 'Database not configured'}), 503
            
        from sqlalchemy import select, func
        from .models import User, Problem, UserProblemProgress
        try:
            db: Session = SessionLocal()
            try:
                user = db.get(User, DEMO_USER_ID)
                if not user:
                    return jsonify({'error': 'NotFound', 'message': 'User not found'}), 404
                total_problems = db.scalar(select(func.count(Problem.id))) or 0
                total_correct = db.scalar(select(func.count(UserProblemProgress.id)).where(
                    UserProblemProgress.user_id == DEMO_USER_ID,
                    UserProblemProgress.is_correct == True
                )) or 0
                progress = (total_correct / total_problems) if total_problems else 0.0
                return jsonify({
                    "user_id": user.id,
                    "username": user.username,
                    "total_xp": user.total_xp,
                    "streak": {"current": user.current_streak, "best": user.best_streak},
                    "progress": round(progress, 4)
                })
            finally:
                db.close()
        except OperationalError as e:
            return jsonify({'error': 'DatabaseError', 'message': 'Database connection failed'}), 503
        except Exception as e:
            return jsonify({'error': 'InternalError', 'message': str(e)}), 500 