"""baseline schema

Revision ID: 20260605_0001
Revises: 
Create Date: 2026-06-05 14:20:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260605_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(), nullable=True),
    )
    op.create_index("ix_users_id", "users", ["id"], unique=False)
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    op.create_table(
        "questions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("reference_answer", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(), nullable=True),
    )
    op.create_index("ix_questions_id", "questions", ["id"], unique=False)

    op.create_table(
        "interviews",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("difficulty", sa.String(length=20), nullable=True),
        sa.Column("knowledge_points", sa.Text(), nullable=True),
        sa.Column("total_rounds", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column("start_time", sa.TIMESTAMP(), nullable=True),
        sa.Column("end_time", sa.TIMESTAMP(), nullable=True),
        sa.Column("repo_context", sa.Text(), nullable=True),
        sa.Column("custom_questions", sa.Text(), nullable=True),
        sa.Column("resume_persona", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_interviews_id", "interviews", ["id"], unique=False)

    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("interview_id", sa.Integer(), nullable=False),
        sa.Column("sender", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=True),
        sa.Column("audio_path", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(), nullable=True),
        sa.ForeignKeyConstraint(["interview_id"], ["interviews.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_messages_id", "messages", ["id"], unique=False)

    op.create_table(
        "evaluations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("interview_id", sa.Integer(), nullable=False),
        sa.Column("content_score", sa.Float(), nullable=True),
        sa.Column("expression_score", sa.Float(), nullable=True),
        sa.Column("business_scenario_score", sa.Float(), nullable=True),
        sa.Column("problem_solving_score", sa.Float(), nullable=True),
        sa.Column("total_score", sa.Float(), nullable=True),
        sa.Column("speech_rate_score", sa.Float(), nullable=True),
        sa.Column("clarity_score", sa.Float(), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("report_json", sa.Text(), nullable=True),
        sa.Column("recommendations", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(), nullable=True),
        sa.ForeignKeyConstraint(["interview_id"], ["interviews.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("interview_id"),
    )
    op.create_index("ix_evaluations_id", "evaluations", ["id"], unique=False)

    op.create_table(
        "voice_metrics",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("interview_id", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.Integer(), nullable=False),
        sa.Column("duration_sec", sa.Float(), nullable=True),
        sa.Column("wpm", sa.Float(), nullable=True),
        sa.Column("pause_ratio", sa.Float(), nullable=True),
        sa.Column("long_pause_count", sa.Integer(), nullable=True),
        sa.Column("filler_total", sa.Integer(), nullable=True),
        sa.Column("pitch_mean", sa.Float(), nullable=True),
        sa.Column("pitch_std", sa.Float(), nullable=True),
        sa.Column("volume_mean", sa.Float(), nullable=True),
        sa.Column("volume_std", sa.Float(), nullable=True),
        sa.Column("raw_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(), nullable=True),
        sa.ForeignKeyConstraint(["interview_id"], ["interviews.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_voice_metrics_id", "voice_metrics", ["id"], unique=False)
    op.create_index("idx_interview", "voice_metrics", ["interview_id"], unique=False)

    op.create_table(
        "code_problems",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("difficulty", sa.String(length=20), nullable=False),
        sa.Column("tags", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("input_format", sa.Text(), nullable=False),
        sa.Column("output_format", sa.Text(), nullable=False),
        sa.Column("samples", sa.Text(), nullable=False),
        sa.Column("constraints", sa.Text(), nullable=False),
        sa.Column("starter_code", sa.Text(), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(), nullable=True),
        sa.Column("updated_at", sa.TIMESTAMP(), nullable=True),
    )
    op.create_index("ix_code_problems_id", "code_problems", ["id"], unique=False)
    op.create_index("ix_code_problems_slug", "code_problems", ["slug"], unique=True)
    op.create_index("idx_code_problems_order", "code_problems", ["order_index"], unique=False)

    op.create_table(
        "code_test_cases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("problem_id", sa.Integer(), nullable=False),
        sa.Column("input", sa.Text(), nullable=False),
        sa.Column("expected_output", sa.Text(), nullable=False),
        sa.Column("is_sample", sa.Boolean(), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(), nullable=True),
        sa.ForeignKeyConstraint(["problem_id"], ["code_problems.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_code_test_cases_id", "code_test_cases", ["id"], unique=False)
    op.create_index("ix_code_test_cases_problem_id", "code_test_cases", ["problem_id"], unique=False)

    op.create_table(
        "code_submissions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("problem_id", sa.Integer(), nullable=False),
        sa.Column("language", sa.String(length=30), nullable=False),
        sa.Column("source_code", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("runtime", sa.Float(), nullable=True),
        sa.Column("memory", sa.Integer(), nullable=True),
        sa.Column("passed_count", sa.Integer(), nullable=True),
        sa.Column("total_count", sa.Integer(), nullable=True),
        sa.Column("stdout", sa.Text(), nullable=True),
        sa.Column("stderr", sa.Text(), nullable=True),
        sa.Column("compile_output", sa.Text(), nullable=True),
        sa.Column("result_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(), nullable=True),
        sa.ForeignKeyConstraint(["problem_id"], ["code_problems.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_code_submissions_id", "code_submissions", ["id"], unique=False)
    op.create_index("ix_code_submissions_problem_id", "code_submissions", ["problem_id"], unique=False)
    op.create_index("ix_code_submissions_user_id", "code_submissions", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_code_submissions_user_id", table_name="code_submissions")
    op.drop_index("ix_code_submissions_problem_id", table_name="code_submissions")
    op.drop_index("ix_code_submissions_id", table_name="code_submissions")
    op.drop_table("code_submissions")

    op.drop_index("ix_code_test_cases_problem_id", table_name="code_test_cases")
    op.drop_index("ix_code_test_cases_id", table_name="code_test_cases")
    op.drop_table("code_test_cases")

    op.drop_index("idx_code_problems_order", table_name="code_problems")
    op.drop_index("ix_code_problems_slug", table_name="code_problems")
    op.drop_index("ix_code_problems_id", table_name="code_problems")
    op.drop_table("code_problems")

    op.drop_index("idx_interview", table_name="voice_metrics")
    op.drop_index("ix_voice_metrics_id", table_name="voice_metrics")
    op.drop_table("voice_metrics")

    op.drop_index("ix_evaluations_id", table_name="evaluations")
    op.drop_table("evaluations")

    op.drop_index("ix_messages_id", table_name="messages")
    op.drop_table("messages")

    op.drop_index("ix_interviews_id", table_name="interviews")
    op.drop_table("interviews")

    op.drop_index("ix_questions_id", table_name="questions")
    op.drop_table("questions")

    op.drop_index("ix_users_username", table_name="users")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_table("users")
