"""add unique constraint to weather forecasts

Revision ID: 772f5c6ba139
Revises: b87209dd38e8
Create Date: 2026-09-13
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "772f5c6ba139"
down_revision: Union[str, Sequence[str], None] = "b87209dd38e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_weather_forecast_field_date",
        "weather_forecasts",
        ["field_id", "forecast_date"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_weather_forecast_field_date",
        "weather_forecasts",
        type_="unique",
    )
