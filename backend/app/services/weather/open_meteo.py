from abc import ABC
from datetime import date
from typing import Any

import httpx

from app.services.weather.base import WeatherProvider


class OpenMeteoProvider(WeatherProvider):
    """
    Weather provider implementation using Open-Meteo.
    """

    FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
    ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

    TIMEOUT_SECONDS = 20.0

    # ============================================================
    # WEATHER CODE MAPPING
    # ============================================================

    @staticmethod
    def weather_code_to_condition(weather_code: int | None) -> str:
        """
        Convert Open-Meteo WMO weather code to a human-readable
        FarmIQ weather condition.
        """

        if weather_code is None:
            return "Unknown"

        # Clear
        if weather_code == 0:
            return "Clear / Sunny"

        # Mainly clear / partly cloudy / overcast
        if weather_code == 1:
            return "Mainly Clear"

        if weather_code == 2:
            return "Partly Cloudy"

        if weather_code == 3:
            return "Overcast"

        # Fog
        if weather_code in (45, 48):
            return "Fog"

        # Drizzle
        if weather_code in (51, 53, 55):
            return "Drizzle"

        if weather_code in (56, 57):
            return "Freezing Drizzle"

        # Rain
        if weather_code in (61, 63, 65):
            return "Rain"

        if weather_code in (66, 67):
            return "Freezing Rain"

        # Snow
        if weather_code in (71, 73, 75, 77):
            return "Snow"

        # Rain showers
        if weather_code in (80, 81, 82):
            return "Rain Showers"

        # Snow showers
        if weather_code in (85, 86):
            return "Snow Showers"

        # Thunderstorms
        if weather_code == 95:
            return "Thunderstorm"

        if weather_code in (96, 99):
            return "Thunderstorm with Hail"

        return "Unknown"

    # ============================================================
    # HTTP
    # ============================================================

    def _get(
        self,
        url: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:

        try:
            with httpx.Client(timeout=self.TIMEOUT_SECONDS) as client:

                response = client.get(
                    url,
                    params=params,
                )

                response.raise_for_status()

                data = response.json()

                if not isinstance(data, dict):
                    raise ValueError(
                        "Open-Meteo returned an invalid response."
                    )

                return data

        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"Open-Meteo HTTP error: {exc.response.status_code}"
            ) from exc

        except httpx.RequestError as exc:
            raise RuntimeError(
                f"Open-Meteo connection error: {exc}"
            ) from exc

        except ValueError as exc:
            raise RuntimeError(
                f"Open-Meteo returned invalid JSON: {exc}"
            ) from exc

    # ============================================================
    # CURRENT WEATHER
    # ============================================================

    def get_current_weather(
        self,
        latitude: float,
        longitude: float,
    ) -> dict[str, Any]:

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": ",".join(
                [
                    "temperature_2m",
                    "relative_humidity_2m",
                    "apparent_temperature",
                    "precipitation",
                    "wind_speed_10m",
                    "wind_direction_10m",
                    "surface_pressure",
                    "weather_code",
                ]
            ),
            "timezone": "auto",
        }

        data = self._get(
            self.FORECAST_URL,
            params,
        )

        current = data.get("current", {})

        weather_code = current.get("weather_code")

        return {
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude"),
            "observed_at": current.get("time"),
            "temperature_c": current.get("temperature_2m"),
            "feels_like_c": current.get("apparent_temperature"),
            "humidity_percent": current.get(
                "relative_humidity_2m"
            ),
            "rainfall_mm": current.get("precipitation"),
            "wind_speed_kmh": current.get(
                "wind_speed_10m"
            ),
            "wind_direction": current.get(
                "wind_direction_10m"
            ),
            "pressure_hpa": current.get(
                "surface_pressure"
            ),
            "weather_code": weather_code,
            "weather_condition": self.weather_code_to_condition(
                weather_code
            ),
            "source": "OPEN_METEO",
        }

    # ============================================================
    # FORECAST
    # ============================================================

    def get_forecast(
        self,
        latitude: float,
        longitude: float,
        forecast_days: int = 7,
    ) -> list[dict[str, Any]]:

        if forecast_days < 1 or forecast_days > 16:
            raise ValueError(
                "forecast_days must be between 1 and 16."
            )

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "forecast_days": forecast_days,
            "daily": ",".join(
                [
                    "temperature_2m_mean",
                    "temperature_2m_min",
                    "temperature_2m_max",
                    "relative_humidity_2m_mean",
                    "precipitation_sum",
                    "precipitation_probability_max",
                    "wind_speed_10m_max",
                    "weather_code",
                ]
            ),
            "timezone": "auto",
        }

        data = self._get(
            self.FORECAST_URL,
            params,
        )

        daily = data.get("daily", {})

        dates = daily.get("time", [])
        temperatures = daily.get(
            "temperature_2m_mean",
            [],
        )
        min_temperatures = daily.get(
            "temperature_2m_min",
            [],
        )
        max_temperatures = daily.get(
            "temperature_2m_max",
            [],
        )
        humidity = daily.get(
            "relative_humidity_2m_mean",
            [],
        )
        rainfall = daily.get(
            "precipitation_sum",
            [],
        )
        rain_probability = daily.get(
            "precipitation_probability_max",
            [],
        )
        wind_speed = daily.get(
            "wind_speed_10m_max",
            [],
        )
        weather_codes = daily.get(
            "weather_code",
            [],
        )

        results = []

        for i, forecast_date in enumerate(dates):

            weather_code = self._get_value(
                weather_codes,
                i,
            )

            results.append(
                {
                    "forecast_date": forecast_date,
                    "temperature_c": self._get_value(
                        temperatures,
                        i,
                    ),
                    "temperature_min_c": self._get_value(
                        min_temperatures,
                        i,
                    ),
                    "temperature_max_c": self._get_value(
                        max_temperatures,
                        i,
                    ),
                    "humidity_percent": self._get_value(
                        humidity,
                        i,
                    ),
                    "rain_probability": self._get_value(
                        rain_probability,
                        i,
                    ),
                    "rainfall_mm": self._get_value(
                        rainfall,
                        i,
                    ),
                    "wind_speed_kmh": self._get_value(
                        wind_speed,
                        i,
                    ),
                    "weather_code": weather_code,
                    "weather_condition": self.weather_code_to_condition(
                        weather_code
                    ),
                    "source": "OPEN_METEO",
                }
            )

        return results

    # ============================================================
    # HISTORICAL WEATHER
    # ============================================================

    def get_historical_weather(
        self,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date,
    ) -> list[dict[str, Any]]:

        if end_date < start_date:
            raise ValueError(
                "end_date cannot be before start_date."
            )

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "daily": ",".join(
                [
                    "temperature_2m_mean",
                    "temperature_2m_min",
                    "temperature_2m_max",
                    "precipitation_sum",
                    "wind_speed_10m_max",
                    "weather_code",
                ]
            ),
            "timezone": "auto",
        }

        data = self._get(
            self.ARCHIVE_URL,
            params,
        )

        daily = data.get("daily", {})

        dates = daily.get("time", [])
        temperatures = daily.get(
            "temperature_2m_mean",
            [],
        )
        min_temperatures = daily.get(
            "temperature_2m_min",
            [],
        )
        max_temperatures = daily.get(
            "temperature_2m_max",
            [],
        )
        rainfall = daily.get(
            "precipitation_sum",
            [],
        )
        wind_speed = daily.get(
            "wind_speed_10m_max",
            [],
        )
        weather_codes = daily.get(
            "weather_code",
            [],
        )

        results = []

        for i, weather_date in enumerate(dates):

            weather_code = self._get_value(
                weather_codes,
                i,
            )

            results.append(
                {
                    "date": weather_date,
                    "temperature_c": self._get_value(
                        temperatures,
                        i,
                    ),
                    "temperature_min_c": self._get_value(
                        min_temperatures,
                        i,
                    ),
                    "temperature_max_c": self._get_value(
                        max_temperatures,
                        i,
                    ),
                    "rainfall_mm": self._get_value(
                        rainfall,
                        i,
                    ),
                    "wind_speed_kmh": self._get_value(
                        wind_speed,
                        i,
                    ),
                    "weather_code": weather_code,
                    "weather_condition": self.weather_code_to_condition(
                        weather_code
                    ),
                    "source": "OPEN_METEO",
                }
            )

        return results

    # ============================================================
    # SAFE ARRAY ACCESS
    # ============================================================

    @staticmethod
    def _get_value(
        values: list[Any],
        index: int,
    ) -> Any:

        if index >= len(values):
            return None

        return values[index]