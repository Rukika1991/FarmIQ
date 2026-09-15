"""add market intelligence tables

Revision ID: 84a37a40c5c2
Revises: 772f5c6ba139
Create Date: 2026-09-14 21:49:08.455125

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.

revision: str = "84a37a40c5c2"

down_revision: Union[str, Sequence[str], None] = "772f5c6ba139"

branch_labels: Union[str, Sequence[str], None] = None

depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create Market Intelligence tables."""

    # ========================================================
    # MARKETS
    # ========================================================

    op.create_table(
        "markets",

        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "name",
            sa.String(length=150),
            nullable=False,
        ),

        sa.Column(
            "country",
            sa.String(length=100),
            nullable=False,
        ),

        sa.Column(
            "region",
            sa.String(length=100),
            nullable=True,
        ),

        sa.Column(
            "district",
            sa.String(length=100),
            nullable=True,
        ),

        sa.Column(
            "city",
            sa.String(length=100),
            nullable=True,
        ),

        sa.Column(
            "latitude",
            sa.Numeric(
                precision=10,
                scale=7,
            ),
            nullable=True,
        ),

        sa.Column(
            "longitude",
            sa.Numeric(
                precision=10,
                scale=7,
            ),
            nullable=True,
        ),

        sa.Column(
            "market_level",
            sa.String(length=30),
            nullable=False,
        ),

        sa.Column(
            "market_type",
            sa.String(length=50),
            nullable=True,
        ),

        sa.Column(
            "currency",
            sa.String(length=10),
            nullable=False,
        ),

        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
        ),

        sa.Column(
            "source",
            sa.String(length=150),
            nullable=True,
        ),

        sa.Column(
            "notes",
            sa.Text(),
            nullable=True,
        ),

        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_markets_id"),
        "markets",
        ["id"],
        unique=False,
    )


    # ========================================================
    # MARKET PRICES
    # ========================================================

    op.create_table(
        "market_prices",

        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "market_id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "crop_id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "price_date",
            sa.DateTime(),
            nullable=False,
        ),

        sa.Column(
            "price",
            sa.Numeric(
                precision=14,
                scale=4,
            ),
            nullable=False,
        ),

        sa.Column(
            "currency",
            sa.String(length=10),
            nullable=False,
        ),

        sa.Column(
            "unit",
            sa.String(length=30),
            nullable=False,
        ),

        sa.Column(
            "min_price",
            sa.Numeric(
                precision=14,
                scale=4,
            ),
            nullable=True,
        ),

        sa.Column(
            "max_price",
            sa.Numeric(
                precision=14,
                scale=4,
            ),
            nullable=True,
        ),

        sa.Column(
            "source",
            sa.String(length=150),
            nullable=False,
        ),

        sa.Column(
            "source_reference",
            sa.String(length=500),
            nullable=True,
        ),

        sa.Column(
            "quality_grade",
            sa.String(length=100),
            nullable=True,
        ),

        sa.Column(
            "notes",
            sa.Text(),
            nullable=True,
        ),

        sa.ForeignKeyConstraint(
            ["market_id"],
            ["markets.id"],
        ),

        sa.ForeignKeyConstraint(
            ["crop_id"],
            ["crops.id"],
        ),

        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_market_prices_id"),
        "market_prices",
        ["id"],
        unique=False,
    )


    # ========================================================
    # PRICE FORECASTS
    # ========================================================

    op.create_table(
        "price_forecasts",

        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "market_id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "crop_id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "forecast_date",
            sa.DateTime(),
            nullable=False,
        ),

        sa.Column(
            "predicted_price",
            sa.Numeric(
                precision=14,
                scale=4,
            ),
            nullable=False,
        ),

        sa.Column(
            "lower_price",
            sa.Numeric(
                precision=14,
                scale=4,
            ),
            nullable=True,
        ),

        sa.Column(
            "upper_price",
            sa.Numeric(
                precision=14,
                scale=4,
            ),
            nullable=True,
        ),

        sa.Column(
            "currency",
            sa.String(length=10),
            nullable=False,
        ),

        sa.Column(
            "unit",
            sa.String(length=30),
            nullable=False,
        ),

        sa.Column(
            "confidence",
            sa.Numeric(
                precision=5,
                scale=2,
            ),
            nullable=True,
        ),

        sa.Column(
            "model_name",
            sa.String(length=100),
            nullable=True,
        ),

        sa.Column(
            "model_version",
            sa.String(length=50),
            nullable=True,
        ),

        sa.Column(
            "generated_at",
            sa.DateTime(),
            nullable=False,
        ),

        sa.Column(
            "source",
            sa.String(length=150),
            nullable=True,
        ),

        sa.Column(
            "notes",
            sa.Text(),
            nullable=True,
        ),

        sa.ForeignKeyConstraint(
            ["market_id"],
            ["markets.id"],
        ),

        sa.ForeignKeyConstraint(
            ["crop_id"],
            ["crops.id"],
        ),

        sa.PrimaryKeyConstraint("id"),

        sa.UniqueConstraint(
            "market_id",
            "crop_id",
            "forecast_date",
            "model_version",
            name="uq_price_forecast_market_crop_date_model",
        ),
    )

    op.create_index(
        op.f("ix_price_forecasts_id"),
        "price_forecasts",
        ["id"],
        unique=False,
    )


def downgrade() -> None:
    """Remove Market Intelligence tables."""

    op.drop_index(
        op.f("ix_price_forecasts_id"),
        table_name="price_forecasts",
    )

    op.drop_table("price_forecasts")

    op.drop_index(
        op.f("ix_market_prices_id"),
        table_name="market_prices",
    )

    op.drop_table("market_prices")

    op.drop_index(
        op.f("ix_markets_id"),
        table_name="markets",
    )

    op.drop_table("markets")
