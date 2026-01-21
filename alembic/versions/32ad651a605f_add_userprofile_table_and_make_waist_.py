"""Add UserProfile table and make waist/neck optional

Revision ID: 32ad651a605f
Revises: 98484fda9450
Create Date: 2026-01-20 16:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '32ad651a605f'
down_revision: Union[str, None] = '98484fda9450'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create user_profiles table
    op.create_table('user_profiles',
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('user_id')
    )

    # For SQLite, we need to recreate the measurements table to make waist/neck nullable
    # First, drop the old indices
    op.drop_index('ix_measurements_date', table_name='measurements')
    op.drop_index('ix_measurements_user_id', table_name='measurements')

    # Create a temporary table with the new schema
    op.create_table('measurements_new',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('weight', sa.Float(), nullable=False),
        sa.Column('waist', sa.Float(), nullable=True),
        sa.Column('neck', sa.Float(), nullable=True),
        sa.Column('calories', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'date', name='uix_user_date')
    )

    # Copy data from old table to new table
    op.execute('''
        INSERT INTO measurements_new (id, user_id, date, weight, waist, neck, calories, created_at)
        SELECT id, user_id, date, weight, waist, neck, calories, created_at
        FROM measurements
    ''')

    # Drop old table
    op.drop_table('measurements')

    # Rename new table to measurements
    op.rename_table('measurements_new', 'measurements')

    # Recreate indices
    op.create_index(op.f('ix_measurements_date'), 'measurements', ['date'], unique=False)
    op.create_index(op.f('ix_measurements_user_id'), 'measurements', ['user_id'], unique=False)


def downgrade() -> None:
    # Drop user_profiles table
    op.drop_table('user_profiles')

    # Recreate measurements table with NOT NULL constraints
    op.create_table('measurements_new',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('weight', sa.Float(), nullable=False),
        sa.Column('waist', sa.Float(), nullable=False),
        sa.Column('neck', sa.Float(), nullable=False),
        sa.Column('calories', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'date', name='uix_user_date')
    )
    op.create_index(op.f('ix_measurements_date'), 'measurements_new', ['date'], unique=False)
    op.create_index(op.f('ix_measurements_user_id'), 'measurements_new', ['user_id'], unique=False)

    # Copy data
    op.execute('''
        INSERT INTO measurements_new (id, user_id, date, weight, waist, neck, calories, created_at)
        SELECT id, user_id, date, weight, waist, neck, calories, created_at
        FROM measurements
        WHERE waist IS NOT NULL AND neck IS NOT NULL
    ''')

    # Drop and rename
    op.drop_table('measurements')
    op.rename_table('measurements_new', 'measurements')
