"""add interview state machine fields

Revision ID: 20260605_0002
Revises: 20260605_0001
Create Date: 2026-06-05 19:20:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260605_0002"
down_revision = "20260605_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("interviews") as batch_op:
        batch_op.add_column(sa.Column("phase", sa.String(length=20), nullable=True, server_default="introduction"))
        batch_op.add_column(sa.Column("knowledge_round_index", sa.Integer(), nullable=True, server_default="0"))
        batch_op.add_column(sa.Column("active_code_problem_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("active_code_submission_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("asked_question_titles", sa.Text(), nullable=True))

    op.execute("UPDATE interviews SET phase = 'introduction' WHERE phase IS NULL")
    op.execute("UPDATE interviews SET knowledge_round_index = 0 WHERE knowledge_round_index IS NULL")


def downgrade() -> None:
    with op.batch_alter_table("interviews") as batch_op:
        batch_op.drop_column("asked_question_titles")
        batch_op.drop_column("active_code_submission_id")
        batch_op.drop_column("active_code_problem_id")
        batch_op.drop_column("knowledge_round_index")
        batch_op.drop_column("phase")
