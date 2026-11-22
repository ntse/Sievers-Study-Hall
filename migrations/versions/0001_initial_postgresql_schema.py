"""Initial PostgreSQL schema

Revision ID: 0001
Revises:
Create Date: 2026-11-22 17:48:04.842821

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_user_email"), ["email"], unique=True)

    op.create_table(
        "bookmarks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("unit", sa.String(length=64), nullable=False),
        sa.Column("exercise", sa.Integer(), nullable=False),
        sa.Column("level", sa.String(length=8), nullable=False),
        sa.Column("result", sa.String(length=10), nullable=False),
        sa.Column("user_answer", sa.Text(), nullable=True),
        sa.Column("feedback_message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "user_exercise_state",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("unit", sa.String(length=64), nullable=False),
        sa.Column("exercise", sa.Integer(), nullable=False),
        sa.Column("state", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id", "unit", "exercise", name="uq_user_unit_exercise"
        ),
    )
    with op.batch_alter_table("user_exercise_state", schema=None) as batch_op:
        batch_op.create_index("idx_unit_exercise", ["unit", "exercise"], unique=False)
        batch_op.create_index(
            batch_op.f("ix_user_exercise_state_user_id"), ["user_id"], unique=False
        )

    op.create_table(
        "user_settings",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("settings", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
        ),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_table(
        "user_unit_home_progress",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("unit", sa.String(length=100), nullable=False),
        sa.Column("completed_exercises", sa.Integer(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
        ),
        sa.PrimaryKeyConstraint("user_id", "unit"),
    )


def downgrade():
    op.drop_table("user_unit_home_progress")
    op.drop_table("user_settings")
    with op.batch_alter_table("user_exercise_state", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_user_exercise_state_user_id"))
        batch_op.drop_index("idx_unit_exercise")

    op.drop_table("user_exercise_state")
    op.drop_table("bookmarks")
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_user_email"))

    op.drop_table("user")
