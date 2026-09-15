from __future__ import annotations

from datetime import datetime
from typing import Any


class WeatherIntelligenceService:
    """
    Agriculture-focused weather intelligence engine.

    This class contains the weather risk rules only.
    It must NOT import itself or WeatherService.
    """

    HEAVY_RAIN_MM = 20.0
    MODERATE_RAIN_MM = 5.0

    HIGH_RAIN_PROBABILITY = 70.0

    HIGH_TEMPERATURE_C = 30.0
    EXTREME_TEMPERATURE_C = 35.0

    STRONG_WIND_KMH = 30.0

    DRY_DAY_RAINFALL_MM = 1.0
    DRY_SPELL_DAYS = 3

    # Potato-specific threshold
    POTATO_HEAVY_RAIN_MM = 15.0

    def analyze_forecast(
        self,
        forecasts: list[dict[str, Any]],
        crop: dict[str, Any] | None = None,
        crop_season: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        risks: list[dict[str, Any]] = []
        recommendations: list[str] = []

        if not forecasts:
            return {
                "risk_level": "LOW",
                "summary": "No weather forecast data available.",
                "risks": [],
                "recommendations": [
                    "No weather forecast data is available for this field."
                ],
            }

        # ---------------------------------------------------------
        # GENERAL WEATHER ANALYSIS
        # ---------------------------------------------------------

        for forecast in forecasts:
            forecast_date = forecast.get("date")

            rainfall = self._to_float(
                forecast.get("rainfall_mm")
            )

            rain_probability = self._to_float(
                forecast.get("rain_probability")
            )

            temperature = self._to_float(
                forecast.get("temperature_c")
            )

            temperature_max = self._to_float(
                forecast.get("temperature_max_c")
            )

            wind_speed = self._to_float(
                forecast.get("wind_speed_kmh")
            )

            # -----------------------------------------------------
            # HEAVY RAIN
            # -----------------------------------------------------

            if rainfall >= self.HEAVY_RAIN_MM:
                risks.append(
                    self._risk(
                        risk_type="HEAVY_RAIN",
                        severity="HIGH",
                        date=forecast_date,
                        message=(
                            f"Heavy rainfall expected "
                            f"({rainfall:.1f} mm)."
                        ),
                    )
                )

            # -----------------------------------------------------
            # MODERATE RAIN
            # -----------------------------------------------------

            elif rainfall >= self.MODERATE_RAIN_MM:
                risks.append(
                    self._risk(
                        risk_type="MODERATE_RAIN",
                        severity="MEDIUM",
                        date=forecast_date,
                        message=(
                            f"Moderate rainfall expected "
                            f"({rainfall:.1f} mm)."
                        ),
                    )
                )

            # -----------------------------------------------------
            # HIGH RAIN PROBABILITY
            # -----------------------------------------------------

            if rain_probability >= self.HIGH_RAIN_PROBABILITY:
                risks.append(
                    self._risk(
                        risk_type="HIGH_RAIN_PROBABILITY",
                        severity="MEDIUM",
                        date=forecast_date,
                        message=(
                            f"High probability of rain "
                            f"({rain_probability:.0f}%)."
                        ),
                    )
                )

            # -----------------------------------------------------
            # HIGH TEMPERATURE
            # -----------------------------------------------------

            effective_temperature = max(
                temperature,
                temperature_max,
            )

            if effective_temperature >= self.EXTREME_TEMPERATURE_C:
                risks.append(
                    self._risk(
                        risk_type="EXTREME_HEAT",
                        severity="HIGH",
                        date=forecast_date,
                        message=(
                            f"Extreme temperature expected "
                            f"({effective_temperature:.1f} °C)."
                        ),
                    )
                )

            elif effective_temperature >= self.HIGH_TEMPERATURE_C:
                risks.append(
                    self._risk(
                        risk_type="HIGH_TEMPERATURE",
                        severity="MEDIUM",
                        date=forecast_date,
                        message=(
                            f"High temperature expected "
                            f"({effective_temperature:.1f} °C)."
                        ),
                    )
                )

            # -----------------------------------------------------
            # STRONG WIND
            # -----------------------------------------------------

            if wind_speed >= self.STRONG_WIND_KMH:
                risks.append(
                    self._risk(
                        risk_type="STRONG_WIND",
                        severity="MEDIUM",
                        date=forecast_date,
                        message=(
                            f"Strong winds expected "
                            f"({wind_speed:.1f} km/h)."
                        ),
                    )
                )

        # ---------------------------------------------------------
        # DRY SPELL ANALYSIS
        # ---------------------------------------------------------

        dry_days = 0

        for forecast in forecasts:
            rainfall = self._to_float(
                forecast.get("rainfall_mm")
            )

            if rainfall < self.DRY_DAY_RAINFALL_MM:
                dry_days += 1

                if dry_days >= self.DRY_SPELL_DAYS:
                    risks.append(
                        self._risk(
                            risk_type="DRY_SPELL",
                            severity="MEDIUM",
                            date=forecast.get("date"),
                            message=(
                                f"A dry spell of at least "
                                f"{self.DRY_SPELL_DAYS} days "
                                f"may occur."
                            ),
                        )
                    )
                    break
            else:
                dry_days = 0

        # ---------------------------------------------------------
        # GENERAL RECOMMENDATIONS
        # ---------------------------------------------------------

        has_rain = any(
            self._to_float(f.get("rainfall_mm"))
            >= self.MODERATE_RAIN_MM
            for f in forecasts
        )

        has_high_rain_probability = any(
            self._to_float(f.get("rain_probability"))
            >= self.HIGH_RAIN_PROBABILITY
            for f in forecasts
        )

        has_heat = any(
            max(
                self._to_float(f.get("temperature_c")),
                self._to_float(f.get("temperature_max_c")),
            )
            >= self.HIGH_TEMPERATURE_C
            for f in forecasts
        )

        if has_rain or has_high_rain_probability:
            recommendations.append(
                "Plan field activities around expected rainfall."
            )

        if has_heat:
            recommendations.append(
                "Monitor soil moisture and crop water requirements "
                "during warmer periods."
            )

        # ---------------------------------------------------------
        # CROP-SPECIFIC ANALYSIS
        # ---------------------------------------------------------

        if crop:
            crop_name = str(
                crop.get("name", "")
            ).strip().lower()

            if crop_name in {
                "irish potato",
                "potato",
                "solanum tuberosum",
            }:
                potato_risks, potato_recommendations = (
                    self._analyze_potato(forecasts)
                )

                risks.extend(potato_risks)
                recommendations.extend(
                    potato_recommendations
                )

        # ---------------------------------------------------------
        # CROP SEASON ANALYSIS
        # ---------------------------------------------------------

        if crop_season:
            recommendations.extend(
                self._analyze_crop_season(
                    crop_season
                )
            )

        # ---------------------------------------------------------
        # REMOVE DUPLICATES
        # ---------------------------------------------------------

        risks = self._deduplicate_risks(risks)

        recommendations = self._deduplicate_recommendations(
            recommendations
        )

        # ---------------------------------------------------------
        # FINAL RISK LEVEL
        # ---------------------------------------------------------

        risk_level = self._calculate_risk_level(risks)

        summary = self._build_summary(
            risk_level=risk_level,
            risks=risks,
        )

        return {
            "risk_level": risk_level,
            "summary": summary,
            "risks": risks,
            "recommendations": recommendations,
        }

    # =============================================================
    # POTATO ANALYSIS
    # =============================================================

    def _analyze_potato(
        self,
        forecasts: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], list[str]]:

        risks: list[dict[str, Any]] = []
        recommendations: list[str] = []

        for forecast in forecasts:
            rainfall = self._to_float(
                forecast.get("rainfall_mm")
            )

            rain_probability = self._to_float(
                forecast.get("rain_probability")
            )

            forecast_date = forecast.get("date")

            # Potato excessive moisture risk
            if rainfall >= self.POTATO_HEAVY_RAIN_MM:
                risks.append(
                    self._risk(
                        risk_type="POTATO_EXCESS_MOISTURE",
                        severity="HIGH",
                        date=forecast_date,
                        message=(
                            f"Heavy rainfall may create excessive "
                            f"soil moisture for Irish potato "
                            f"({rainfall:.1f} mm expected)."
                        ),
                    )
                )

            # High probability of rainfall
            if rain_probability >= self.HIGH_RAIN_PROBABILITY:
                recommendations.append(
                    "For Irish potato, avoid unnecessary fertilizer "
                    "or foliar applications immediately before heavy "
                    "rainfall."
                )

        if any(
            self._to_float(
                f.get("rainfall_mm")
            ) >= self.POTATO_HEAVY_RAIN_MM
            for f in forecasts
        ):
            recommendations.append(
                "Check Irish potato fields for poor drainage "
                "and waterlogging after heavy rainfall."
            )

            recommendations.append(
                "Monitor Irish potato crops closely for fungal "
                "diseases during prolonged wet conditions."
            )

        return risks, recommendations

    # =============================================================
    # CROP SEASON ANALYSIS
    # =============================================================

    def _analyze_crop_season(
        self,
        crop_season: dict[str, Any],
    ) -> list[str]:

        recommendations: list[str] = []

        status = str(
            crop_season.get("status", "")
        ).upper()

        if status in {"PLANTED", "ACTIVE", "GROWING"}:
            recommendations.append(
                "The crop is currently in the field. "
                "Use the weather forecast to plan field "
                "operations and crop protection activities."
            )

        expected_harvest = crop_season.get(
            "expected_harvest_date"
        )

        if expected_harvest:
            try:
                if isinstance(
                    expected_harvest,
                    datetime,
                ):
                    harvest_date = expected_harvest
                else:
                    harvest_date = datetime.fromisoformat(
                        str(expected_harvest)
                    )

                days_until_harvest = (
                    harvest_date.date()
                    - datetime.utcnow().date()
                ).days

                if 0 <= days_until_harvest <= 7:
                    recommendations.append(
                        "Harvest is approaching. Monitor rainfall "
                        "and soil conditions and prepare for timely "
                        "harvesting."
                    )

            except (ValueError, TypeError):
                pass

        return recommendations

    # =============================================================
    # HELPERS
    # =============================================================

    @staticmethod
    def _to_float(value: Any) -> float:
        if value is None:
            return 0.0

        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _risk(
        risk_type: str,
        severity: str,
        date: Any,
        message: str,
    ) -> dict[str, Any]:

        return {
            "risk_type": risk_type,
            "severity": severity,
            "date": date,
            "message": message,
        }

    @staticmethod
    def _severity_score(
        severity: str,
    ) -> int:

        scores = {
            "LOW": 1,
            "MEDIUM": 2,
            "HIGH": 3,
            "CRITICAL": 4,
        }

        return scores.get(
            str(severity).upper(),
            1,
        )

    def _calculate_risk_level(
        self,
        risks: list[dict[str, Any]],
    ) -> str:

        if not risks:
            return "LOW"

        highest_score = max(
            self._severity_score(
                risk.get("severity", "LOW")
            )
            for risk in risks
        )

        if highest_score >= 4:
            return "CRITICAL"

        if highest_score >= 3:
            return "HIGH"

        if highest_score >= 2:
            return "MEDIUM"

        return "LOW"

    @staticmethod
    def _deduplicate_risks(
        risks: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:

        unique = []
        seen = set()

        for risk in risks:
            key = (
                risk.get("risk_type"),
                risk.get("severity"),
                str(risk.get("date")),
                risk.get("message"),
            )

            if key not in seen:
                seen.add(key)
                unique.append(risk)

        return unique

    @staticmethod
    def _deduplicate_recommendations(
        recommendations: list[str],
    ) -> list[str]:

        unique = []
        seen = set()

        for recommendation in recommendations:
            if recommendation not in seen:
                seen.add(recommendation)
                unique.append(recommendation)

        return unique

    @staticmethod
    def _build_summary(
        risk_level: str,
        risks: list[dict[str, Any]],
    ) -> str:

        if risk_level == "CRITICAL":
            return (
                "Critical weather risks detected. "
                "Immediate farm management action is recommended."
            )

        if risk_level == "HIGH":
            return (
                "High weather risks detected. "
                "Farmers should take preventive action."
            )

        if risk_level == "MEDIUM":
            return (
                "Moderate weather risks detected. "
                "Farmers should monitor conditions."
            )

        if risks:
            return (
                "Low weather risks detected. "
                "Normal farm monitoring is recommended."
            )

        return (
            "Weather conditions appear generally favorable "
            "based on the available forecast."
        )
