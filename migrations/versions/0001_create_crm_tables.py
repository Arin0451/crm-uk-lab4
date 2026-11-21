"""Create CRM tables.

Revision ID: 0001
"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "employees",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("full_name", sa.String(120), nullable=False),
        sa.Column("role", sa.String(80), nullable=False),
    )
    op.create_table(
        "residents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("full_name", sa.String(120), nullable=False),
        sa.Column("address", sa.String(200), nullable=False),
    )
    op.create_table(
        "service_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("resident_id", sa.Integer(), nullable=False),
        sa.Column("assignee_id", sa.Integer(), nullable=True),
        sa.Column("subject", sa.String(160), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(80), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "accepted", "assigned", "suspended", "closed",
                name="ck_service_requests_status",
                native_enum=False,
                create_constraint=True,
            ),
            server_default="accepted",
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False,
        ),
        sa.CheckConstraint(
            "status NOT IN ('assigned', 'closed') OR assignee_id IS NOT NULL",
            name="ck_service_requests_assignee_required",
        ),
        sa.ForeignKeyConstraint(["assignee_id"], ["employees.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["resident_id"], ["residents.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_service_requests_assignee_id", "service_requests", ["assignee_id"])
    op.create_index("ix_service_requests_resident_id", "service_requests", ["resident_id"])


def downgrade() -> None:
    op.drop_table("service_requests")
    op.drop_table("residents")
    op.drop_table("employees")
