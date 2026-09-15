"""add weather tables

Revision ID: b87209dd38e8
Revises: 917e8bb48c3a
Create Date: 2026-09-13 09:22:33.207870

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# ============================================================
# REVISION IDENTIFIERS
# ============================================================

revision: str = "b87209dd38e8"

down_revision: Union[str, Sequence[str], None] = "917e8bb48c3a"

branch_labels: Union[str, Sequence[str], None] = None

depends_on: Union[str, Sequence[str], None] = None


# ============================================================
# UPGRADE
# ============================================================

def upgrade() -> None:
    """Create Weather Intelligence tables."""

    # --------------------------------------------------------
    # WEATHER ALERTS
    # --------------------------------------------------------

    op.create_table(
        "weather_alerts",

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
            "alert_type",
            sa.String(length=50),
            nullable=False,
        ),

        sa.Column(
            "severity",
            sa.String(length=20),
            nullable=False,
        ),

        sa.Column(
            "title",
            sa.String(length=200),
            nullable=False,
        ),

        sa.Column(
            "message",
            sa.Text(),
            nullable=False,
        ),

        sa.Column(
            "start_time",
            sa.DateTime(),
            nullable=True,
        ),

        sa.Column(
            "end_time",
            sa.DateTime(),
            nullable=True,
        ),

        sa.Column(
            "source",
            sa.String(length=50),
            nullable=False,
        ),

        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),

        sa.ForeignKeyConstraint(
            ["field_id"],
            ["fields.id"],
        ),
    )

    op.create_index(
        "ix_weather_alerts_id",
        "weather_alerts",
        ["id"],
        unique=False,
    )

    op.create_index(
        "ix_weather_alerts_field_id",
        "weather_alerts",
        ["field_id"],
        unique=False,
    )


    # --------------------------------------------------------
    # WEATHER FORECASTS
    # --------------------------------------------------------

    op.create_table(
        "weather_forecasts",

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
            "forecast_date",
            sa.DateTime(),
            nullable=False,
        ),

        sa.Column(
            "forecast_time",
            sa.DateTime(),
            nullable=True,
        ),

        sa.Column(
            "temperature_c",
            sa.Numeric(precision=6, scale=2),
            nullable=True,
        ),

        sa.Column(
            "temperature_min_c",
            sa.Numeric(precision=6, scale=2),
            nullable=True,
        ),

        sa.Column(
            "temperature_max_c",
            sa.Numeric(precision=6, scale=2),
            nullable=True,
        ),

        sa.Column(
            "humidity_percent",
            sa.Numeric(precision=5, scale=2),
            nullable=True,
        ),

        sa.Column(
            "rain_probability",
            sa.Numeric(precision=5, scale=2),
            nullable=True,
        ),

        sa.Column(
            "rainfall_mm",
            sa.Numeric(precision=8, scale=2),
            nullable=True,
        ),

        sa.Column(
            "wind_speed_kmh",
            sa.Numeric(precision=8, scale=2),
            nullable=True,
        ),

        sa.Column(
            "weather_condition",
            sa.String(length=100),
            nullable=True,
        ),

        sa.Column(
            "source",
            sa.String(length=50),
            nullable=False,
        ),

        sa.ForeignKeyConstraint(
            ["field_id"],
            ["fields.id"],
        ),
    )

    op.create_index(
        "ix_weather_forecasts_id",
        "weather_forecasts",
        ["id"],
        unique=False,
    )

    op.create_index(
        "ix_weather_forecasts_field_id",
        "weather_forecasts",
        ["field_id"],
        unique=False,
    )

    op.create_index(
        "ix_weather_forecasts_forecast_date",
        "weather_forecasts",
        ["forecast_date"],
        unique=False,
    )


    # --------------------------------------------------------
    # WEATHER OBSERVATIONS
    # --------------------------------------------------------

    op.create_table(
        "weather_observations",

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
            "observed_at",
            sa.DateTime(),
            nullable=False,
        ),

        sa.Column(
            "temperature_c",
            sa.Numeric(precision=6, scale=2),
            nullable=True,
        ),

        sa.Column(
            "feels_like_c",
            sa.Numeric(precision=6, scale=2),
            nullable=True,
        ),

        sa.Column(
            "humidity_percent",
            sa.Numeric(precision=5, scale=2),
            nullable=True,
        ),

        sa.Column(
            "rainfall_mm",
            sa.Numeric(precision=8, scale=2),
            nullable=True,
        ),

        sa.Column(
            "wind_speed_kmh",
            sa.Numeric(precision=8, scale=2),
            nullable=True,
        ),

        sa.Column(
            "wind_direction",
            sa.String(length=20),
            nullable=True,
        ),

        sa.Column(
            "pressure_hpa",
            sa.Numeric(precision=8, scale=2),
            nullable=True,
        ),

        sa.Column(
            "weather_condition",
            sa.String(length=100),
            nullable=True,
        ),

        sa.Column(
            "source",
            sa.String(length=50),
            nullable=False,
        ),

        sa.ForeignKeyConstraint(
            ["field_id"],
            ["fields.id"],
        ),
    )

    op.create_index(
        "ix_weather_observations_id",
        "weather_observations",
        ["id"],
        unique=False,
    )

    op.create_index(
        "ix_weather_observations_field_id",
        "weather_observations",
        ["field_id"],
        unique=False,
    )

    op.create_index(
        "ix_weather_observations_observed_at",
        "weather_observations",
        ["observed_at"],
        unique=False,
    )


# ============================================================
# DOWNGRADE
# ============================================================

def downgrade() -> None:
    """Remove Weather Intelligence tables."""

    # Weather observations
    op.drop_index(
        "ix_weather_observations_observed_at",
        table_name="weather_observations",
    )

    op.drop_index(
        "ix_weather_observations_field_id",
        table_name="weather_observations",
    )

    op.drop_index(
        "ix_weather_observations_id",
        table_name="weather_observations",
    )

    op.drop_table("weather_observations")


    # Weather forecasts
    op.drop_index(
        "ix_weather_forecasts_forecast_date",
        table_name="weather_forecasts",
    )

    op.drop_index(
        "ix_weather_forecasts_field_id",
        table_name="weather_forecasts",
    )

    op.drop_index(
        "ix_weather_forecasts_id",
        table_name="weather_forecasts",
    )

    op.drop_table("weather_forecasts")


    # Weather alerts
    op.drop_index(
        "ix_weather_alerts_field_id",
        table_name="weather_alerts",
    )

    op.drop_index(
        "ix_weather_alerts_id",
        table_name="weather_alerts",
    )

    op.drop_table("weather_alerts")