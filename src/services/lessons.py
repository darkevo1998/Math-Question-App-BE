from typing import Iterable
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from ..models import Lesson, Problem, ProblemOption, UserProblemProgress, UserProgress


def get_lessons_with_progress(db: Session, user_id: int):
    lessons = db.execute(select(Lesson).order_by(Lesson.order_index)).scalars().all()
    result = []
    for lesson in lessons:
        total_problems = db.scalar(select(func.count(Problem.id)).where(Problem.lesson_id == lesson.id)) or 0
        correct = db.scalar(
            select(func.count(UserProblemProgress.id))
            .join(Problem, Problem.id == UserProblemProgress.problem_id)
            .where(UserProblemProgress.user_id == user_id, Problem.lesson_id == lesson.id, UserProblemProgress.is_correct == True)
        ) or 0
        progress = (correct / total_problems) if total_problems else 0.0
        result.append({
            "id": lesson.id,
            "title": lesson.title,
            "description": lesson.description,
            "progress": round(progress, 4),
            "total_problems": total_problems,
            "correct": correct,
        })
    return result


def get_lesson_detail(db: Session, user_id: int, lesson_id: int):
    lesson = db.get(Lesson, lesson_id)
    if not lesson:
        return None
    problems = db.execute(select(Problem).where(Problem.lesson_id == lesson_id).order_by(Problem.id)).scalars().all()
    problem_dicts = []
    for p in problems:
        item = {
            "id": p.id,
            "type": p.type,
            "prompt": p.prompt,
        }
        if p.type == "mcq":
            options = db.execute(select(ProblemOption).where(ProblemOption.problem_id == p.id).order_by(ProblemOption.id)).scalars().all()
            item["options"] = [{"id": o.id, "text": o.text} for o in options]  # do not leak is_correct
        problem_dicts.append(item)
    total_problems = len(problems)
    correct = db.scalar(
        select(func.count(UserProblemProgress.id))
        .join(Problem, Problem.id == UserProblemProgress.problem_id)
        .where(UserProblemProgress.user_id == user_id, Problem.lesson_id == lesson_id, UserProblemProgress.is_correct == True)
    ) or 0
    progress = (correct / total_problems) if total_problems else 0.0
    return {
        "id": lesson.id,
        "title": lesson.title,
        "description": lesson.description,
        "problems": problem_dicts,
        "progress": round(progress, 4),
    } 