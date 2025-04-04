"""create corpuses table

Revision ID: b177664d4828
Revises: 90f98994c0d4
Create Date: 2025-03-21 13:13:48.068528

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b177664d4828'
down_revision: Union[str, None] = '90f98994c0d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('Corpuses',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('corpus_name', sa.String(), nullable=True),
    sa.Column('text', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_Corpuses_corpus_name'), 'Corpuses', ['corpus_name'], unique=True)
    op.create_index(op.f('ix_Corpuses_id'), 'Corpuses', ['id'], unique=False)
    op.drop_column('Users', 'token')
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Users', sa.Column('token', sa.VARCHAR(), nullable=True))
    op.drop_index(op.f('ix_Corpuses_id'), table_name='Corpuses')
    op.drop_index(op.f('ix_Corpuses_corpus_name'), table_name='Corpuses')
    op.drop_table('Corpuses')
    # ### end Alembic commands ###
