from datetime import date, datetime
from typing import Any

from app.models.models import Field, CropSeason
from sqlalchemy.orm import Session

from app.models.models import Field
from app.models.weather import (
    WeatherForecast,
    WeatherObservation,
)
from app.services.weather.open_meteo import OpenMeteoProvider
from app.services.weather.weather_intelligence import (
    WeatherIntelligenceService,
)


class WeatherService:
    """
    Database-aware weather service for FarmIQ.

    Responsibilities:
    - Read field coordinates
    - Fetch weather from the configured provider
    - Save current observations
    - Save/update forecasts
    - Retrieve historical weather
    - Retrieve saved weather history
    - Generate agricultural weather intelligence
    """

    def __init__(
        self,
        db: Session,
        provider: OpenMeteoProvider | None = None,
    ):
        self.db = db
        self.provider = provider or OpenMeteoProvider()

    # ============================================================
    # FIELD
    # ============================================================

    def _get_field(self, field_id: int) -> Field:
        field = (
            self.db.query(Field)
            .filter(Field.id == field_id)
            .first()
        )

        if not field:
            raise ValueError("Field not found.")

        if field.latitude is None or field.longitude is None:
            raise ValueError(
                "Field does not have latitude and longitude."
            )

        return field

          # ============================================================
    # ACTIVE CROP SEASON
    # ============================================================

    def _get_active_crop_season(
        self,
        field_id: int,
    ) -> CropSeason | None:
        """
        Get the most relevant crop season for a field.

        Priority:
        1. ACTIVE crop season
        2. PLANTED crop season
        3. Most recent crop season
        """

        crop_season = (
            self.db.query(CropSeason)
            .filter(
                CropSeason.field_id == field_id,
                CropSeason.status == "ACTIVE",
            )
            .order_by(
                CropSeason.planting_date.desc()
            )
            .first()
        )

        if crop_season:
            return crop_season

        crop_season = (
            self.db.query(CropSeason)
            .filter(
                CropSeason.field_id == field_id,
                CropSeason.status == "PLANTED",
            )
            .order_by(
                CropSeason.planting_date.desc()
            )
            .first()
        )

        if crop_season:
            return crop_season

        return (
            self.db.query(CropSeason)
            .filter(
                CropSeason.field_id == field_id
            )
            .order_by(
                CropSeason.planting_date.desc()
            )
            .first()
        )

    # ============================================================
    # CURRENT WEATHER
    # ============================================================

    def get_current_weather(
        self,
        field_id: int,
        save: bool = True,
    ) -> dict[str, Any]:

        field = self._get_field(field_id)

        weather = self.provider.get_current_weather(
            float(field.latitude),
            float(field.longitude),
        )

        if save:
            self._save_observation(
                field_id=field.id,
                weather=weather,
            )

        return weather

    # ============================================================
    # SAVE CURRENT OBSERVATION
    # ============================================================

    def _save_observation(
        self,
        field_id: int,
        weather: dict[str, Any],
    ) -> WeatherObservation:

        observed_at_value = weather.get("observed_at")

        if observed_at_value:
            try:
                observed_at = datetime.fromisoformat(
                    observed_at_value
                )
            except (TypeError, ValueError):
                observed_at = datetime.utcnow()
        else:
            observed_at = datetime.utcnow()

        observation = WeatherObservation(
            field_id=field_id,
            observed_at=observed_at,
            temperature_c=weather.get("temperature_c"),
            feels_like_c=weather.get("feels_like_c"),
            humidity_percent=weather.get(
                "humidity_percent"
            ),
            rainfall_mm=weather.get("rainfall_mm"),
            wind_speed_kmh=weather.get(
                "wind_speed_kmh"
            ),
            wind_direction=weather.get(
                "wind_direction"
            ),
            pressure_hpa=weather.get(
                "pressure_hpa"
            ),
            weather_condition=weather.get(
                "weather_condition"
            ),
            source=weather.get(
                "source",
                "OPEN_METEO",
            ),
        )

        self.db.add(observation)
        self.db.commit()
        self.db.refresh(observation)

        return observation

    # ============================================================
    # FORECAST
    # ============================================================

    def get_forecast(
        self,
        field_id: int,
        forecast_days: int = 7,
        save: bool = True,
    ) -> list[Any]:

        field = self._get_field(field_id)

        forecasts = self.provider.get_forecast(
            float(field.latitude),
            float(field.longitude),
            forecast_days,
        )

        if save:
            return self._save_forecasts(
                field_id=field.id,
                forecasts=forecasts,
            )

        return forecasts

    # ============================================================
    # SAVE / UPDATE FORECASTS
    # ============================================================

    def _save_forecasts(
        self,
        field_id: int,
        forecasts: list[dict[str, Any]],
    ) -> list[WeatherForecast]:

        saved = []

        try:
            for forecast in forecasts:

                forecast_date_value = forecast.get(
                    "forecast_date"
                )

                if not forecast_date_value:
                    continue

                try:
                    forecast_date = datetime.fromisoformat(
                        forecast_date_value
                    )
                except (TypeError, ValueError):
                    continue

                # ------------------------------------------------
                # Check whether this forecast already exists
                # for this field and date.
                # ------------------------------------------------

                record = (
                    self.db.query(WeatherForecast)
                    .filter(
                        WeatherForecast.field_id == field_id,
                        WeatherForecast.forecast_date
                        == forecast_date,
                    )
                    .first()
                )

                # ------------------------------------------------
                # Create new record
                # ------------------------------------------------

                if not record:
                    record = WeatherForecast(
                        field_id=field_id,
                        forecast_date=forecast_date,
                        forecast_time=None,
                    )

                    self.db.add(record)

                # ------------------------------------------------
                # Update weather information
                # ------------------------------------------------

                record.temperature_c = forecast.get(
                    "temperature_c"
                )

                record.temperature_min_c = forecast.get(
                    "temperature_min_c"
                )

                record.temperature_max_c = forecast.get(
                    "temperature_max_c"
                )

                record.humidity_percent = forecast.get(
                    "humidity_percent"
                )

                record.rain_probability = forecast.get(
                    "rain_probability"
                )

                record.rainfall_mm = forecast.get(
                    "rainfall_mm"
                )

                record.wind_speed_kmh = forecast.get(
                    "wind_speed_kmh"
                )

                record.weather_condition = forecast.get(
                    "weather_condition"
                )

                record.source = forecast.get(
                    "source",
                    "OPEN_METEO",
                )

                saved.append(record)

            self.db.commit()

            for record in saved:
                self.db.refresh(record)

            return saved

        except Exception:
            self.db.rollback()
            raise

    # ============================================================
    # WEATHER INTELLIGENCE
    # ============================================================

    def get_weather_intelligence(
        self,
        field_id: int,
        forecast_days: int = 7,
    ) -> dict[str, Any]:
        """
        Analyze weather forecasts for a field using:

        - weather forecast
        - active crop season
        - crop information
        - agriculture-specific intelligence rules
        """

        # --------------------------------------------------------
        # GET FIELD
        # --------------------------------------------------------

        field = self._get_field(field_id)

        # --------------------------------------------------------
        # GET ACTIVE CROP SEASON
        # --------------------------------------------------------

        crop_season = self._get_active_crop_season(field.id)

        # --------------------------------------------------------
        # GET FORECAST
        # --------------------------------------------------------

        forecasts = self.get_forecast(
            field_id=field_id,
            forecast_days=forecast_days,
            save=True,
        )

        # --------------------------------------------------------
        # CONVERT FORECAST OBJECTS TO INTELLIGENCE DATA
        # --------------------------------------------------------

        forecast_data = []

        for forecast in forecasts:
            forecast_data.append(
                {
                    "date": forecast.forecast_date,
                    "temperature_c": forecast.temperature_c,
                    "temperature_min_c": forecast.temperature_min_c,
                    "temperature_max_c": forecast.temperature_max_c,
                    "humidity_percent": forecast.humidity_percent,
                    "rain_probability": forecast.rain_probability,
                    "rainfall_mm": forecast.rainfall_mm,
                    "wind_speed_kmh": forecast.wind_speed_kmh,
                    "weather_condition": forecast.weather_condition,
                    "source": forecast.source,
                }
            )

        # --------------------------------------------------------
        # BUILD CROP DATA
        # --------------------------------------------------------

        crop_data = None
        crop_season_data = None

        if (
            crop_season is not None
            and crop_season.crop is not None
        ):
            crop_data = {
                "id": crop_season.crop.id,
                "name": crop_season.crop.name,
                "scientific_name": crop_season.crop.scientific_name,
            }

            crop_season_data = {
                "id": crop_season.id,
                "status": crop_season.status,
                "variety": crop_season.variety,
                "planting_date": crop_season.planting_date,
                "expected_harvest_date": (
                    crop_season.expected_harvest_date
                ),
                "area_hectares": crop_season.area_hectares,
            }

        # --------------------------------------------------------
        # RUN INTELLIGENCE ENGINE
        # --------------------------------------------------------

        intelligence_service = WeatherIntelligenceService()

        return intelligence_service.analyze_forecast(
            forecasts=forecast_data,
            crop=crop_data,
            crop_season=crop_season_data,
        )

    # ============================================================
    # HISTORICAL WEATHER
    # ============================================================

    def get_historical_weather(
        self,
        field_id: int,
        start_date: date,
        end_date: date,
    ) -> list[dict[str, Any]]:

        field = self._get_field(field_id)

        return self.provider.get_historical_weather(
            float(field.latitude),
            float(field.longitude),
            start_date,
            end_date,
        )

    # ============================================================
    # DATABASE OBSERVATION HISTORY
    # ============================================================

    def get_saved_observations(
        self,
        field_id: int,
        limit: int = 100,
    ) -> list[WeatherObservation]:

        self._get_field(field_id)

        return (
            self.db.query(WeatherObservation)
            .filter(
                WeatherObservation.field_id == field_id
            )
            .order_by(
                WeatherObservation.observed_at.desc()
            )
            .limit(limit)
            .all()
        )

    # ============================================================
    # DATABASE FORECAST HISTORY
    # ============================================================

    def get_saved_forecasts(
        self,
        field_id: int,
        limit: int = 100,
    ) -> list[WeatherForecast]:

        self._get_field(field_id)

        return (
            self.db.query(WeatherForecast)
            .filter(
                WeatherForecast.field_id == field_id
            )
            .order_by(
                WeatherForecast.forecast_date.asc()
            )
            .limit(limit)
            .all()
        )

    # ============================================================
    # ROLLBACK HELPER
    # ============================================================

    def rollback(self) -> None:
        self.db.rollback()
