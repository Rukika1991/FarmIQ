"""create FarmIQ initial schema

Revision ID: 982fe75f51a7
Revises:
Create Date: 2026-09-12

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "982fe75f51a7"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the initial FarmIQ database schema."""

    # ============================================================
    # USERS
    # ============================================================

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("full_name", sa.String(length=150), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column(
            "hashed_password",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "role",
            sa.String(length=50),
            nullable=False,
            server_default="FARMER",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )

    op.create_index(
        "ix_users_id",
        "users",
        ["id"],
        unique=False,
    )

    op.create_index(
        "ix_users_email",
        "users",
        ["email"],
        unique=True,
    )

    # ============================================================
    # FARMERS
    # ============================================================

    op.create_table(
        "farmers",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("phone", sa.String(length=30), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.UniqueConstraint(
            "user_id",
            name="uq_farmers_user_id",
        ),
    )

    op.create_index(
        "ix_farmers_id",
        "farmers",
        ["id"],
        unique=False,
    )

    # ============================================================
    # FARMS
    # ============================================================

    op.create_table(
        "farms",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("farmer_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("district", sa.String(length=100), nullable=False),
        sa.Column("sector", sa.String(length=100), nullable=True),
        sa.Column("village", sa.String(length=100), nullable=True),
        sa.Column(
            "latitude",
            sa.Numeric(precision=10, scale=7),
            nullable=True,
        ),
        sa.Column(
            "longitude",
            sa.Numeric(precision=10, scale=7),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["farmer_id"],
            ["farmers.id"],
        ),
    )

    op.create_index(
        "ix_farms_id",
        "farms",
        ["id"],
        unique=False,
    )

    # ============================================================
    # FIELDS
    # ============================================================

    op.create_table(
        "fields",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("farm_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column(
            "area_hectares",
            sa.Numeric(precision=10, scale=4),
            nullable=False,
        ),
        sa.Column(
            "latitude",
            sa.Numeric(precision=10, scale=7),
            nullable=True,
        ),
        sa.Column(
            "longitude",
            sa.Numeric(precision=10, scale=7),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["farm_id"],
            ["farms.id"],
        ),
    )

    op.create_index(
        "ix_fields_id",
        "fields",
        ["id"],
        unique=False,
    )

    # ============================================================
    # SOIL PROFILES
    # ============================================================

    op.create_table(
        "soil_profiles",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("field_id", sa.Integer(), nullable=False),

        # LABORATORY = priority 1
        # LOCATION_ESTIMATE = priority 2
        sa.Column(
            "source",
            sa.String(length=50),
            nullable=False,
        ),

        sa.Column(
            "ph",
            sa.Numeric(precision=5, scale=2),
            nullable=True,
        ),
        sa.Column(
            "nitrogen",
            sa.Numeric(precision=12, scale=4),
            nullable=True,
        ),
        sa.Column(
            "phosphorus",
            sa.Numeric(precision=12, scale=4),
            nullable=True,
        ),
        sa.Column(
            "potassium",
            sa.Numeric(precision=12, scale=4),
            nullable=True,
        ),
        sa.Column(
            "organic_carbon",
            sa.Numeric(precision=8, scale=4),
            nullable=True,
        ),
        sa.Column(
            "texture",
            sa.String(length=100),
            nullable=True,
        ),
        sa.Column(
            "soil_depth_cm",
            sa.Numeric(precision=8, scale=2),
            nullable=True,
        ),
        sa.Column(
            "drainage",
            sa.String(length=100),
            nullable=True,
        ),
        sa.Column(
            "confidence",
            sa.String(length=30),
            nullable=False,
            server_default="MEDIUM",
        ),
        sa.Column(
            "test_date",
            sa.DateTime(),
            nullable=True,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            "notes",
            sa.Text(),
            nullable=True,
        ),

        sa.ForeignKeyConstraint(
            ["field_id"],
            ["fields.id"],
        ),
    )

    op.create_index(
        "ix_soil_profiles_id",
        "soil_profiles",
        ["id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop the initial FarmIQ database schema."""

    op.drop_index(
        "ix_soil_profiles_id",
        table_name="soil_profiles",
    )
    op.drop_table("soil_profiles")

    op.drop_index(
        "ix_fields_id",
        table_name="fields",
    )
    op.drop_table("fields")

    op.drop_index(
        "ix_farms_id",
        table_name="farms",
    )
    op.drop_table("farms")

    op.drop_index(
        "ix_farmers_id",
        table_name="farmers",
    )
    op.drop_table("farmers")

    op.drop_index(
        "ix_users_email",
        table_name="users",
    )
    op.drop_index(
        "ix_users_id",
        table_name="users",
    )
    op.drop_table("users")
