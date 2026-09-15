from datetime import date, timedelta
from statistics import mean

from sqlalchemy.orm import Session

from app.models.market import MarketPrice


# ============================================================
# FARM IQ MARKET PRICE FORECASTING
# ============================================================


class MarketForecastingService:
    """
    FarmIQ market price forecasting service.

    Version 2:
    - Historical data validation
    - Linear trend regression
    - Forecast price
    - Prediction range
    - Confidence score
    - Market trend classification

    IMPORTANT:
    This is a baseline forecasting model.
    It should later be compared with stronger models using
    sufficient real historical market data.
    """

    MINIMUM_OBSERVATIONS = 7
    DEFAULT_LOOKBACK_DAYS = 30

    # --------------------------------------------------------
    # INITIALIZE SERVICE
    # --------------------------------------------------------

    def __init__(self, db: Session):
        self.db = db

    # --------------------------------------------------------
    # GET HISTORICAL PRICES
    # --------------------------------------------------------

    def get_historical_prices(
        self,
        market_id: int,
        crop_id: int,
        lookback_days: int = DEFAULT_LOOKBACK_DAYS,
    ):
        end_date = date.today()

        start_date = (
            end_date
            - timedelta(days=lookback_days)
        )

        prices = (
            self.db.query(MarketPrice)
            .filter(
                MarketPrice.market_id == market_id,
                MarketPrice.crop_id == crop_id,
                MarketPrice.price_date >= start_date,
                MarketPrice.price_date <= end_date,
            )
            .order_by(
                MarketPrice.price_date.asc()
            )
            .all()
        )

        return prices

    # --------------------------------------------------------
    # VALIDATE HISTORICAL DATA
    # --------------------------------------------------------

    def validate_historical_data(
        self,
        prices,
    ):
        observation_count = len(prices)

        if observation_count < self.MINIMUM_OBSERVATIONS:
            return {
                "ready": False,
                "observation_count": observation_count,
                "minimum_required": self.MINIMUM_OBSERVATIONS,
                "message": (
                    "Insufficient historical data for "
                    "forecasting. FarmIQ requires at least "
                    f"{self.MINIMUM_OBSERVATIONS} "
                    "price observations."
                ),
            }

        return {
            "ready": True,
            "observation_count": observation_count,
            "minimum_required": self.MINIMUM_OBSERVATIONS,
            "message": (
                "Sufficient historical data available."
            ),
        }

    # --------------------------------------------------------
    # LINEAR REGRESSION
    # --------------------------------------------------------

    @staticmethod
    def calculate_linear_regression(
        values,
    ):
        """
        Calculate a simple linear regression:

            y = intercept + slope * x

        x = observation sequence
        y = market price
        """

        n = len(values)

        if n < 2:
            raise ValueError(
                "At least two observations are required "
                "for regression."
            )

        x_values = list(
            range(n)
        )

        x_mean = mean(
            x_values
        )

        y_mean = mean(
            values
        )

        numerator = sum(
            (
                x - x_mean
            )
            * (
                y - y_mean
            )
            for x, y in zip(
                x_values,
                values,
            )
        )

        denominator = sum(
            (
                x - x_mean
            ) ** 2
            for x in x_values
        )

        if denominator == 0:
            slope = 0.0
        else:
            slope = (
                numerator
                / denominator
            )

        intercept = (
            y_mean
            - slope * x_mean
        )

        return slope, intercept

    # --------------------------------------------------------
    # R-SQUARED
    # --------------------------------------------------------

    @staticmethod
    def calculate_r_squared(
        values,
        slope,
        intercept,
    ):
        """
        Calculate R-squared.

        R-squared measures how much of the historical
        price variation is explained by the linear trend.
        """

        if not values:
            return 0.0

        x_values = list(
            range(len(values))
        )

        actual_mean = mean(
            values
        )

        predictions = [
            intercept
            + slope * x
            for x in x_values
        ]

        ss_total = sum(
            (
                actual
                - actual_mean
            ) ** 2
            for actual in values
        )

        ss_residual = sum(
            (
                actual
                - predicted
            ) ** 2
            for actual, predicted
            in zip(
                values,
                predictions,
            )
        )

        if ss_total == 0:
            return 1.0

        r_squared = (
            1
            - (
                ss_residual
                / ss_total
            )
        )

        return max(
            0.0,
            min(
                1.0,
                r_squared,
            ),
        )

    # --------------------------------------------------------
    # FORECAST PRICE
    # --------------------------------------------------------

    def forecast_price(
        self,
        market_id: int,
        crop_id: int,
        forecast_days: int = 7,
        lookback_days: int = DEFAULT_LOOKBACK_DAYS,
    ):
        prices = self.get_historical_prices(
            market_id=market_id,
            crop_id=crop_id,
            lookback_days=lookback_days,
        )

        # ----------------------------------------------------
        # Validate data
        # ----------------------------------------------------

        validation = (
            self.validate_historical_data(
                prices
            )
        )

        if not validation["ready"]:
            return {
                "status": "INSUFFICIENT_DATA",
                "market_id": market_id,
                "crop_id": crop_id,
                "forecast_days": forecast_days,
                "observation_count": (
                    validation[
                        "observation_count"
                    ]
                ),
                "minimum_required": (
                    validation[
                        "minimum_required"
                    ]
                ),
                "message": (
                    validation["message"]
                ),
            }

        # ----------------------------------------------------
        # Keep only valid price observations
        # ----------------------------------------------------

        valid_prices = [
            price
            for price in prices
            if price.price is not None
        ]

        values = [
            float(price.price)
            for price in valid_prices
        ]

        if len(values) < self.MINIMUM_OBSERVATIONS:
            return {
                "status": "INSUFFICIENT_DATA",
                "market_id": market_id,
                "crop_id": crop_id,
                "forecast_days": forecast_days,
                "observation_count": len(values),
                "minimum_required": (
                    self.MINIMUM_OBSERVATIONS
                ),
                "message": (
                    "Not enough valid price values "
                    "for forecasting."
                ),
            }

        # ----------------------------------------------------
        # Calculate trend
        # ----------------------------------------------------

        slope, intercept = (
            self.calculate_linear_regression(
                values
            )
        )

        # ----------------------------------------------------
        # Calculate R-squared
        # ----------------------------------------------------

        r_squared = (
            self.calculate_r_squared(
                values,
                slope,
                intercept,
            )
        )

        # ----------------------------------------------------
        # Predict future price
        # ----------------------------------------------------

        future_index = (
            len(values)
            - 1
            + forecast_days
        )

        predicted_price = (
            intercept
            + slope * future_index
        )

        # ----------------------------------------------------
        # Calculate historical prediction errors
        # ----------------------------------------------------

        historical_predictions = [
            intercept
            + slope * x
            for x in range(
                len(values)
            )
        ]

        residuals = [
            actual - predicted
            for actual, predicted
            in zip(
                values,
                historical_predictions,
            )
        ]

        residual_mean = mean(
            residuals
        )

        residual_variance = mean(
            (
                residual
                - residual_mean
            ) ** 2
            for residual in residuals
        )

        residual_std = (
            residual_variance ** 0.5
        )

        # ----------------------------------------------------
        # Prediction interval
        # ----------------------------------------------------

        lower_price = (
            predicted_price
            - 1.96 * residual_std
        )

        upper_price = (
            predicted_price
            + 1.96 * residual_std
        )

        # ----------------------------------------------------
        # Prevent negative prices
        # ----------------------------------------------------

        lower_price = max(
            0.0,
            lower_price,
        )

        predicted_price = max(
            0.0,
            predicted_price,
        )

        upper_price = max(
            predicted_price,
            upper_price,
        )

        # ----------------------------------------------------
        # Confidence score
        # ----------------------------------------------------

        confidence = (
            0.40
            + (
                0.50
                * r_squared
            )
        )

        observation_bonus = min(
            0.10,
            len(values) / 300,
        )

        confidence = min(
            0.95,
            confidence
            + observation_bonus,
        )

        # ----------------------------------------------------
        # Trend classification
        # ----------------------------------------------------

        if slope > 0.5:
            trend = "UPWARD"

        elif slope < -0.5:
            trend = "DOWNWARD"

        else:
            trend = "STABLE"

        # ----------------------------------------------------
        # Forecast date
        # ----------------------------------------------------

        last_date = (
            valid_prices[-1].price_date
        )

        forecast_date = (
            last_date
            + timedelta(
                days=forecast_days
            )
        )

        # ----------------------------------------------------
        # Return forecast
        # ----------------------------------------------------

        return {
            "status": "SUCCESS",

            "market_id": market_id,

            "crop_id": crop_id,

            "last_observation_date": str(
                last_date
            ),

            "forecast_date": str(
                forecast_date
            ),

            "forecast_days": forecast_days,

            "predicted_price": round(
                predicted_price,
                2,
            ),

            "lower_price": round(
                lower_price,
                2,
            ),

            "upper_price": round(
                upper_price,
                2,
            ),

            "currency": (
                valid_prices[-1].currency
            ),

            "unit": (
                valid_prices[-1].unit
            ),

            "confidence": round(
                confidence,
                2,
            ),

            "trend": trend,

            "daily_trend": round(
                slope,
                4,
            ),

            "r_squared": round(
                r_squared,
                4,
            ),

            "observation_count": (
                len(values)
            ),

            "model_name": (
                "LINEAR_TREND_REGRESSION"
            ),

            "model_version": "2.0",
        }
