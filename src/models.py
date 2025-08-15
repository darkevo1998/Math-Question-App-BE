from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, DateTime, Date, ForeignKey, Text, Boolean, UniqueConstraint, Index, Float
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from .db import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True)
    total_xp: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    current_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    best_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_activity_utc_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Lesson(Base):
    __tablename__ = "lessons"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(String(256), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, index=True, nullable=False)


class Problem(Base):
    __tablename__ = "problems"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), index=True)
    type: Mapped[str] = mapped_column(String(16), nullable=False)  # mcq | input
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    # For input problems
    correct_answer_text: Mapped[str | None] = mapped_column(String(64))


class ProblemOption(Base):
    __tablename__ = "problem_options"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id", ondelete="CASCADE"), index=True)
    text: Mapped[str] = mapped_column(String(128), nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class Submission(Base):
    __tablename__ = "submissions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    attempt_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    correct_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    earned_xp: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_xp_after: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    current_streak_after: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    best_streak_after: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    lesson_progress_after: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)


class UserProgress(Base):
    __tablename__ = "user_progress"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"))
    correct_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_problems: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "lesson_id", name="uq_user_lesson_progress"),
        Index("ix_user_progress_user", "user_id"),
        Index("ix_user_progress_lesson", "lesson_id"),
    )


class UserProblemProgress(Base):
    __tablename__ = "user_problem_progress"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id", ondelete="CASCADE"))
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "problem_id", name="uq_user_problem"),
        Index("ix_user_problem_user", "user_id"),
        Index("ix_user_problem_problem", "problem_id"),
    ) 