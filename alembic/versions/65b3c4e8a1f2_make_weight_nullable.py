"""make weight nullable

Revision ID: 65b3c4e8a1f2
Revises: 32ad651a605f
Create Date: 2026-01-21 15:32:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '65b3c4e8a1f2'
down_revision: Union[str, None] = '32ad651a605f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Сделать weight nullable для возможности создания записей только с калориями.
    SQLite требует recreation таблицы.
    """
    # 1. Drop indices if they exist (SQLite-safe approach)
    connection = op.get_bind()

    # Check and drop ix_measurements_date if exists
    try:
        op.drop_index('ix_measurements_date', table_name='measurements')
    except Exception:
        pass  # Index doesn't exist, that's ok

    # Check and drop ix_measurements_user_id if exists
    try:
        op.drop_index('ix_measurements_user_id', table_name='measurements')
    except Exception:
        pass  # Index doesn't exist, that's ok

    # Clean up any leftover temp table from previous failed migration
    try:
        op.drop_table('measurements_new')
    except Exception:
        pass  # Table doesn't exist, that's ok

    # 2. Create new table with nullable weight and calories
    op.create_table(
        'measurements_new',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('weight', sa.Float(), nullable=True),  # Changed to nullable
        sa.Column('waist', sa.Float(), nullable=True),
        sa.Column('neck', sa.Float(), nullable=True),
        sa.Column('calories', sa.Integer(), nullable=True),  # Changed to nullable
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'date', name='_user_date_uc')
    )

    # 3. Copy data from old table (set updated_at = created_at for existing records)
    op.execute('''
        INSERT INTO measurements_new (id, user_id, date, weight, waist, neck, calories, created_at, updated_at)
        SELECT id, user_id, date, weight, waist, neck, calories, created_at, created_at
        FROM measurements
    ''')

    # 4. Drop old table
    op.drop_table('measurements')

    # 5. Rename new table
    op.rename_table('measurements_new', 'measurements')

    # 6. Recreate indices
    op.create_index('ix_measurements_user_id', 'measurements', ['user_id'])
    op.create_index('ix_measurements_date', 'measurements', ['date'])


def downgrade() -> None:
    """
    Revert weight back to non-nullable.
    """
    # 1. Drop indices
    op.drop_index('ix_measurements_date', table_name='measurements')
    op.drop_index('ix_measurements_user_id', table_name='measurements')

    # 2. Create old table structure (weight NOT NULL)
    op.create_table(
        'measurements_new',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('weight', sa.Float(), nullable=False),  # NOT NULL
        sa.Column('waist', sa.Float(), nullable=True),
        sa.Column('neck', sa.Float(), nullable=True),
        sa.Column('calories', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'date', name='_user_date_uc')
    )

    # 3. Copy data (skip records with NULL weight)
    op.execute('''
        INSERT INTO measurements_new (id, user_id, date, weight, waist, neck, calories, created_at, updated_at)
        SELECT id, user_id, date, weight, waist, neck, calories, created_at, updated_at
        FROM measurements
        WHERE weight IS NOT NULL
    ''')

    # 4. Drop old table
    op.drop_table('measurements')

    # 5. Rename new table
    op.rename_table('measurements_new', 'measurements')

    # 6. Recreate indices
    op.create_index('ix_measurements_user_id', 'measurements', ['user_id'])
    op.create_index('ix_measurements_date', 'measurements', ['date'])
