from __future__ import annotations
import os
from dataclasses import dataclass
from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from ..models import Lesson, Problem, ProblemOption, Submission, User, UserProblemProgress
from .streak import calculate_new_streak, utc_today

XP_PER_CORRECT = int(os.getenv("XP_PER_CORRECT", "10"))


class DuplicateAttemptError(Exception):
    pass


class ValidationError(Exception):
    pass


class InvalidProblemError(Exception):
    pass


@dataclass
class AnswerItem:
    problem_id: int
    option_id: int | None = None
    value: str | None = None


def _normalize_value(value: str) -> str:
    return str(value).strip().lower()


def process_submission(db: Session, user_id: int, lesson_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    attempt_id = payload.get("attempt_id")
    answers = payload.get("answers")
    if not attempt_id or not isinstance(attempt_id, str):
        raise ValidationError("attempt_id is required")
    if not answers or not isinstance(answers, list):
        raise ValidationError("answers must be non-empty")

    # Idempotency check
    existing = db.execute(select(Submission).where(Submission.attempt_id == attempt_id)).scalar_one_or_none()
    if existing:
        raise DuplicateAttemptError("This attempt_id was already processed")

    lesson = db.get(Lesson, lesson_id)
    if not lesson:
        raise ValidationError("Lesson not found")

    # Load user
    user = db.get(User, user_id)
    if not user:
        raise ValidationError("User not found")

    # Build problem map for validation
    problems = db.execute(select(Problem).where(Problem.lesson_id == lesson_id)).scalars().all()
    problem_by_id = {p.id: p for p in problems}
    if not problems:
        raise ValidationError("Lesson has no problems")

    correct_count = 0

    for idx, a in enumerate(answers):
        if not isinstance(a, dict):
            raise ValidationError("answer items must be objects")
        problem_id = a.get("problem_id")
        if not isinstance(problem_id, int):
            raise ValidationError("problem_id must be an integer")
        problem = problem_by_id.get(problem_id)
        if not problem:
            raise InvalidProblemError(f"Problem {problem_id} not found")

        if problem.type == "mcq":
            option_id = a.get("option_id")
            if not isinstance(option_id, int):
                raise ValidationError("option_id must be an integer for mcq problems")
            option = db.execute(select(ProblemOption).where(
                ProblemOption.id == option_id,
                ProblemOption.problem_id == problem_id
            )).scalar_one_or_none()
            if not option:
                raise ValidationError(f"option_id {option_id} invalid for problem {problem_id}")
            is_correct = option.is_correct
        elif problem.type == "input":
            value = a.get("value")
            if value is None:
                raise ValidationError("value is required for input problems")
            is_correct = _normalize_value(str(value)) == _normalize_value(problem.correct_answer_text or "")
        else:
            raise ValidationError(f"unknown problem type: {problem.type}")

        if is_correct:
            correct_count += 1
            # Upsert user_problem_progress to mark as correct
            upp = db.execute(select(UserProblemProgress).where(
                UserProblemProgress.user_id == user_id,
                UserProblemProgress.problem_id == problem_id
            )).scalar_one_or_none()
            if upp:
                if not upp.is_correct:
                    upp.is_correct = True
                    db.add(upp)
            else:
                db.add(UserProblemProgress(user_id=user_id, problem_id=problem_id, is_correct=True))

    # Compute XP
    earned_xp = correct_count * XP_PER_CORRECT

    # Streak update logic
    new_streak, incremented, gap = calculate_new_streak(user.last_activity_utc_date, user.current_streak)
    if incremented:
        user.current_streak = new_streak
        user.best_streak = max(user.best_streak, user.current_streak)
        user.last_activity_utc_date = utc_today()

    # Update XP
    user.total_xp = user.total_xp + earned_xp

    # Lesson progress after submission
    total_problems = len(problems)
    total_correct_in_lesson = db.scalar(
        select(func.count(UserProblemProgress.id)).where(
            UserProblemProgress.user_id == user_id,
            UserProblemProgress.problem_id.in_([p.id for p in problems]),
            UserProblemProgress.is_correct == True
        )
    ) or 0
    lesson_progress = (total_correct_in_lesson / total_problems) if total_problems else 0.0

    # Record submission (idempotency key uniqueness ensures no double processing)
    submission = Submission(
        attempt_id=attempt_id,
        user_id=user_id,
        lesson_id=lesson_id,
        correct_count=correct_count,
        earned_xp=earned_xp,
        total_xp_after=user.total_xp,
        current_streak_after=user.current_streak,
        best_streak_after=user.best_streak,
        lesson_progress_after=lesson_progress,
    )
    db.add(user)
    db.add(submission)

    return {
        "correct_count": correct_count,
        "earned_xp": earned_xp,
        "new_total_xp": user.total_xp,
        "streak": {"current": user.current_streak, "best": user.best_streak},
        "lesson_progress": round(lesson_progress, 4),
    } 