from abc import ABC, abstractmethod
from datetime import date
from typing import Any


class WeatherProvider(ABC):
    """
    Abstract interface for weather data providers.

    FarmIQ should depend on this interface rather than directly
    depending on a specific weather provider.
    """

    @abstractmethod
    def get_current_weather(
        self,
        latitude: float,
        longitude: float,
    ) -> dict[str, Any]:
        """
        Get the current weather for a geographic location.
        """
        raise NotImplementedError

    @abstractmethod
    def get_forecast(
        self,
        latitude: float,
        longitude: float,
        forecast_days: int = 7,
    ) -> list[dict[str, Any]]:
        """
        Get daily/hourly forecast data for a geographic location.
        """
        raise NotImplementedError

    @abstractmethod
    def get_historical_weather(
        self,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date,
    ) -> list[dict[str, Any]]:
        """
        Get historical weather data for a geographic location.
        """
        raise NotImplementedError
