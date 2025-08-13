"""
Initial schema for MathQuest
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = "20240801_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(length=64), nullable=False, unique=True),
        sa.Column("total_xp", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("current_streak", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("best_streak", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_activity_utc_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "lessons",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=128), nullable=False),
        sa.Column("description", sa.String(length=256), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
    )
    op.create_index("ix_lessons_order", "lessons", ["order_index"]) 

    op.create_table(
        "problems",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("lesson_id", sa.Integer(), sa.ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.String(length=16), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("correct_answer_text", sa.String(length=64), nullable=True),
    )
    op.create_index("ix_problems_lesson", "problems", ["lesson_id"]) 

    op.create_table(
        "problem_options",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("problem_id", sa.Integer(), sa.ForeignKey("problems.id", ondelete="CASCADE"), nullable=False),
        sa.Column("text", sa.String(length=128), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.create_index("ix_problem_options_problem_id", "problem_options", ["problem_id"]) 

    op.create_table(
        "submissions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("attempt_id", sa.String(length=64), nullable=False, unique=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("lesson_id", sa.Integer(), sa.ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("correct_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("earned_xp", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_xp_after", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("current_streak_after", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("best_streak_after", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("lesson_progress_after", sa.Float(), nullable=False, server_default="0"),
    )
    op.create_index("ix_submissions_attempt_id", "submissions", ["attempt_id"], unique=True)

    op.create_table(
        "user_progress",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("lesson_id", sa.Integer(), sa.ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False),
        sa.Column("correct_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_problems", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("user_id", "lesson_id", name="uq_user_lesson_progress"),
    )
    op.create_index("ix_user_progress_user", "user_progress", ["user_id"]) 
    op.create_index("ix_user_progress_lesson", "user_progress", ["lesson_id"]) 

    op.create_table(
        "user_problem_progress",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("problem_id", sa.Integer(), sa.ForeignKey("problems.id", ondelete="CASCADE"), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.UniqueConstraint("user_id", "problem_id", name="uq_user_problem"),
    )
    op.create_index("ix_user_problem_user", "user_problem_progress", ["user_id"]) 
    op.create_index("ix_user_problem_problem", "user_problem_progress", ["problem_id"]) 


def downgrade() -> None:
    op.drop_index("ix_user_problem_problem", table_name="user_problem_progress")
    op.drop_index("ix_user_problem_user", table_name="user_problem_progress")
    op.drop_table("user_problem_progress")

    op.drop_index("ix_user_progress_lesson", table_name="user_progress")
    op.drop_index("ix_user_progress_user", table_name="user_progress")
    op.drop_table("user_progress")

    op.drop_index("ix_submissions_attempt_id", table_name="submissions")
    op.drop_table("submissions")

    op.drop_index("ix_problem_options_problem_id", table_name="problem_options")
    op.drop_table("problem_options")

    op.drop_index("ix_problems_lesson", table_name="problems")
    op.drop_table("problems")

    op.drop_index("ix_lessons_order", table_name="lessons")
    op.drop_table("lessons")

    op.drop_table("users") 