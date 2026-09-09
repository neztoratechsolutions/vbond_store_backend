"""create categories table

Revision ID: 22d5eec9f086
Revises: ebd26f2c171a
Create Date: 2026-09-08 22:52:25.227433

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '22d5eec9f086'
down_revision: Union[str, Sequence[str], None] = 'ebd26f2c171a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        'categories',

        sa.Column(
            'id',
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            'name',
            sa.String(length=150),
            nullable=False
        ),

        sa.Column(
            'slug',
            sa.String(length=180),
            nullable=False
        ),

        sa.Column(
            'description',
            sa.Text(),
            nullable=True
        ),

        sa.Column(
            'image',
            sa.String(length=255),
            nullable=True
        ),

        sa.Column(
            'is_active',
            sa.Boolean(),
            nullable=True
        ),

        sa.Column(
            'display_order',
            sa.Integer(),
            nullable=True
        ),

        sa.Column(
            'created_at',
            sa.DateTime(),
            nullable=True
        ),

        sa.Column(
            'updated_at',
            sa.DateTime(),
            nullable=True
        ),

        sa.PrimaryKeyConstraint('id'),

        sa.UniqueConstraint(
            'name'
        ),

        sa.UniqueConstraint(
            'slug'
        )
    )

    op.create_index(
        op.f('ix_categories_id'),
        'categories',
        ['id'],
        unique=False
    )

    op.create_index(
        op.f('ix_categories_slug'),
        'categories',
        ['slug'],
        unique=True
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(
        op.f('ix_categories_slug'),
        table_name='categories'
    )

    op.drop_index(
        op.f('ix_categories_id'),
        table_name='categories'
    )

    op.drop_table(
        'categories'
    )