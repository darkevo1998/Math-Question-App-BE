from flask import request
from flask_restx import Api, Resource, Namespace, fields
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from .db import SessionLocal
from .services.lessons import get_lessons_with_progress, get_lesson_detail
from .services.submit import process_submission, DuplicateAttemptError, ValidationError, InvalidProblemError

DEMO_USER_ID = 1

# Create API namespaces
api = Api()
lessons_ns = Namespace('lessons', description='Lesson operations')
profile_ns = Namespace('profile', description='User profile operations')

# Define models for Swagger documentation
lesson_model = api.model('Lesson', {
    'id': fields.Integer(required=True, description='Lesson ID'),
    'title': fields.String(required=True, description='Lesson title'),
    'description': fields.String(required=True, description='Lesson description'),
    'progress': fields.Float(required=True, description='Progress percentage (0-1)'),
    'total_problems': fields.Integer(required=True, description='Total number of problems'),
    'correct': fields.Integer(required=True, description='Number of correct answers'),
})

lesson_detail_model = api.model('LessonDetail', {
    'id': fields.Integer(required=True, description='Lesson ID'),
    'title': fields.String(required=True, description='Lesson title'),
    'description': fields.String(required=True, description='Lesson description'),
    'progress': fields.Float(required=True, description='Progress percentage (0-1)'),
    'problems': fields.List(fields.Raw, required=True, description='List of problems'),
})

problem_model = api.model('Problem', {
    'id': fields.Integer(required=True, description='Problem ID'),
    'type': fields.String(required=True, description='Problem type (mcq or input)'),
    'prompt': fields.String(required=True, description='Problem prompt'),
    'options': fields.List(fields.Raw, description='Multiple choice options (for mcq type)'),
})

option_model = api.model('Option', {
    'id': fields.Integer(required=True, description='Option ID'),
    'text': fields.String(required=True, description='Option text'),
})

answer_model = api.model('Answer', {
    'problem_id': fields.Integer(required=True, description='Problem ID'),
    'option_id': fields.Integer(description='Selected option ID (for mcq problems)'),
    'value': fields.String(description='Answer value (for input problems)'),
})

submit_request_model = api.model('SubmitRequest', {
    'attempt_id': fields.String(required=True, description='Unique attempt identifier'),
    'answers': fields.List(fields.Nested(answer_model), required=True, description='List of answers'),
})

submit_response_model = api.model('SubmitResponse', {
    'correct_count': fields.Integer(required=True, description='Number of correct answers'),
    'earned_xp': fields.Integer(required=True, description='XP earned from this submission'),
    'new_total_xp': fields.Integer(required=True, description='Total XP after submission'),
    'streak': fields.Raw(required=True, description='Current and best streak information'),
    'lesson_progress': fields.Float(required=True, description='Lesson progress after submission'),
})

profile_model = api.model('Profile', {
    'user_id': fields.Integer(required=True, description='User ID'),
    'username': fields.String(required=True, description='Username'),
    'total_xp': fields.Integer(required=True, description='Total XP earned'),
    'streak': fields.Raw(required=True, description='Current and best streak information'),
    'progress': fields.Float(required=True, description='Overall progress percentage'),
})

error_model = api.model('Error', {
    'error': fields.String(required=True, description='Error type'),
    'message': fields.String(required=True, description='Error message'),
})

@lessons_ns.route('/')
class LessonsList(Resource):
    @lessons_ns.doc('list_lessons')
    @lessons_ns.marshal_list_with(lesson_model)
    def get(self):
        """List all lessons with progress for the demo user"""
        db: Session = SessionLocal()
        try:
            items = get_lessons_with_progress(db, DEMO_USER_ID)
            return items
        finally:
            db.close()

@lessons_ns.route('/<int:lesson_id>')
@lessons_ns.param('lesson_id', 'The lesson identifier')
class LessonDetail(Resource):
    @lessons_ns.doc('get_lesson')
    @lessons_ns.marshal_with(lesson_detail_model)
    @lessons_ns.response(404, 'Lesson not found', error_model)
    def get(self, lesson_id):
        """Get lesson details with problems (correct answers not included)"""
        db: Session = SessionLocal()
        try:
            data = get_lesson_detail(db, DEMO_USER_ID, lesson_id)
            if not data:
                lessons_ns.abort(404, error="NotFound", message="Lesson not found")
            return data
        finally:
            db.close()

@lessons_ns.route('/<int:lesson_id>/submit')
@lessons_ns.param('lesson_id', 'The lesson identifier')
class LessonSubmit(Resource):
    @lessons_ns.doc('submit_lesson')
    @lessons_ns.expect(submit_request_model)
    @lessons_ns.marshal_with(submit_response_model)
    @lessons_ns.response(400, 'Validation error', error_model)
    @lessons_ns.response(409, 'Duplicate attempt', error_model)
    @lessons_ns.response(422, 'Invalid problem', error_model)
    def post(self, lesson_id):
        """Submit answers for a lesson (idempotent)"""
        db: Session = SessionLocal()
        try:
            payload = request.get_json(silent=True) or {}
            try:
                result = process_submission(db, DEMO_USER_ID, lesson_id, payload)
                db.commit()
                return result
            except DuplicateAttemptError as e:
                db.rollback()
                lessons_ns.abort(409, error="DuplicateAttempt", message=str(e))
            except InvalidProblemError as e:
                db.rollback()
                lessons_ns.abort(422, error="InvalidProblem", message=str(e))
            except ValidationError as e:
                db.rollback()
                lessons_ns.abort(400, error="Validation", message=str(e))
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

@profile_ns.route('/')
class Profile(Resource):
    @profile_ns.doc('get_profile')
    @profile_ns.marshal_with(profile_model)
    @profile_ns.response(404, 'User not found', error_model)
    def get(self):
        """Get user profile and statistics"""
        from sqlalchemy import select, func
        from .models import User, Problem, UserProblemProgress
        db: Session = SessionLocal()
        try:
            user = db.get(User, DEMO_USER_ID)
            if not user:
                profile_ns.abort(404, error="NotFound", message="User not found")
            total_problems = db.scalar(select(func.count(Problem.id))) or 0
            total_correct = db.scalar(select(func.count(UserProblemProgress.id)).where(
                UserProblemProgress.user_id == DEMO_USER_ID,
                UserProblemProgress.is_correct == True
            )) or 0
            progress = (total_correct / total_problems) if total_problems else 0.0
            return {
                "user_id": user.id,
                "username": user.username,
                "total_xp": user.total_xp,
                "streak": {"current": user.current_streak, "best": user.best_streak},
                "progress": round(progress, 4)
            }
        finally:
            db.close()

def register_routes(api_instance):
    """Register all API namespaces"""
    api_instance.add_namespace(lessons_ns)
    api_instance.add_namespace(profile_ns) 