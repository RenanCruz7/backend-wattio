"""create films table

Revision ID: 20260626_000001
Revises:
Create Date: 2026-06-26 00:00:01

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260626_000001"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "films",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("director", sa.String(length=255), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("genre", sa.String(length=100), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(op.f("ix_films_genre"), "films", ["genre"], unique=False)
    op.create_index(op.f("ix_films_title"), "films", ["title"], unique=False)
    op.create_index(op.f("ix_films_year"), "films", ["year"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_films_year"), table_name="films")
    op.drop_index(op.f("ix_films_title"), table_name="films")
    op.drop_index(op.f("ix_films_genre"), table_name="films")
    op.drop_table("films")
