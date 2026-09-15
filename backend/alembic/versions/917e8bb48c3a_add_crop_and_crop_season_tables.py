"""add crop and crop season tables

Revision ID: 917e8bb48c3a
Revises: 982fe75f51a7
Create Date: 2026-09-13

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "917e8bb48c3a"
down_revision: Union[str, Sequence[str], None] = "982fe75f51a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "crops",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "name",
            sa.String(length=150),
            nullable=False,
        ),
        sa.Column(
            "scientific_name",
            sa.String(length=150),
            nullable=True,
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.UniqueConstraint(
            "name",
            name="uq_crops_name",
        ),
    )

    op.create_index(
        "ix_crops_id",
        "crops",
        ["id"],
        unique=False,
    )

    op.create_table(
        "crop_seasons",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "field_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "crop_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "variety",
            sa.String(length=150),
            nullable=True,
        ),
        sa.Column(
            "area_hectares",
            sa.Numeric(
                precision=10,
                scale=4,
            ),
            nullable=False,
        ),
        sa.Column(
            "planting_date",
            sa.DateTime(),
            nullable=True,
        ),
        sa.Column(
            "expected_harvest_date",
            sa.DateTime(),
            nullable=True,
        ),
        sa.Column(
            "actual_harvest_date",
            sa.DateTime(),
            nullable=True,
        ),
        sa.Column(
            "expected_yield_kg",
            sa.Numeric(
                precision=14,
                scale=2,
            ),
            nullable=True,
        ),
        sa.Column(
            "actual_yield_kg",
            sa.Numeric(
                precision=14,
                scale=2,
            ),
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.String(length=30),
            nullable=False,
            server_default="PLANNED",
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
        sa.ForeignKeyConstraint(
            ["crop_id"],
            ["crops.id"],
        ),
    )

    op.create_index(
        "ix_crop_seasons_id",
        "crop_seasons",
        ["id"],
        unique=False,
    )

    op.create_index(
        "ix_crop_seasons_field_id",
        "crop_seasons",
        ["field_id"],
        unique=False,
    )

    op.create_index(
        "ix_crop_seasons_crop_id",
        "crop_seasons",
        ["crop_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_crop_seasons_crop_id",
        table_name="crop_seasons",
    )

    op.drop_index(
        "ix_crop_seasons_field_id",
        table_name="crop_seasons",
    )

    op.drop_index(
        "ix_crop_seasons_id",
        table_name="crop_seasons",
    )

    op.drop_table("crop_seasons")

    op.drop_index(
        "ix_crops_id",
        table_name="crops",
    )

    op.drop_table("crops")