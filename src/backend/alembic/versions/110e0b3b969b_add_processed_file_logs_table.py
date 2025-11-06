"""Add processed_file_logs table

Revision ID: 110e0b3b969b
Revises: 
Create Date: 2025-11-05 10:37:25.404220

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '110e0b3b969b'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'processed_file_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('file_hash', sa.String(), nullable=False),
        sa.Column('content_hash', sa.String(), nullable=False),
        sa.Column('source_filename', sa.String(), nullable=False),
        sa.Column('processed_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('file_hash', name='uq_file_hash'),
        sa.UniqueConstraint('content_hash', name='uq_content_hash')
    )
    op.create_index('ix_processed_file_logs_file_hash', 'processed_file_logs', ['file_hash'])
    op.create_index('ix_processed_file_logs_content_hash', 'processed_file_logs', ['content_hash'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_processed_file_logs_content_hash', table_name='processed_file_logs')
    op.drop_index('ix_processed_file_logs_file_hash', table_name='processed_file_logs')
    op.drop_table('processed_file_logs')
