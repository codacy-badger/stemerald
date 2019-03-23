"""add notification table

Revision ID: 912786b01dd1
Revises: 546013f4b282
Create Date: 2019-03-23 11:49:27.514386

"""

# revision identifiers, used by Alembic.
revision = '912786b01dd1'
down_revision = '546013f4b282'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('notification',
    sa.Column('removed_at', sa.DateTime(), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('member_id', sa.Integer(), nullable=False),
    sa.Column('read_at', sa.DateTime(), nullable=True),
    sa.Column('title', sa.Unicode(length=100), nullable=False),
    sa.Column('description', sa.Unicode(length=500), nullable=False),
    sa.Column('thumbnail', sa.Unicode(length=500), nullable=True),
    sa.Column('link', sa.Unicode(), nullable=True),
    sa.Column('template', sa.Unicode(length=256), nullable=True),
    sa.Column('body', sa.JSON(), nullable=True),
    sa.Column('severity', sa.Integer(), nullable=False),
    sa.Column('topic', sa.Unicode(length=64), nullable=True),
    sa.Column('content_type', sa.Unicode(length=50), nullable=True),
    sa.Column('target', sa.Unicode(length=50), nullable=True),
    sa.ForeignKeyConstraint(['id'], ['task.id'], ),
    sa.ForeignKeyConstraint(['member_id'], ['member.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('notification')
    # ### end Alembic commands ###
