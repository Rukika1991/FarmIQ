from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Optional


# ============================================================
# NORMALIZED MARKET PRICE RECORD
# ============================================================

@dataclass
class MarketPriceRecord:
    """
    Standard FarmIQ representation of a market price.

    Every external source must eventually be converted into
    this format before being sent to MarketIngestionService.
    """

    market_id: int
    crop_id: int

    price: Decimal
    price_date: datetime

    currency: str
    unit: str

    source: str

    source_reference: Optional[str] = None

    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None

    quality_grade: Optional[str] = None
    notes: Optional[str] = None


# ============================================================
# SOURCE ADAPTER BASE CLASS
# ============================================================

class MarketSourceAdapter:
    """
    Base class for all FarmIQ market-data sources.

    Future adapters:
        FAOAdapter
        EAXAdapter
        CSVAdapter
        MarketOfficerAdapter
        APIAdapter
    """

    source_name = "UNKNOWN"

    def fetch(self, *args, **kwargs) -> list[MarketPriceRecord]:
        """
        Fetch raw market data and convert it into normalized
        FarmIQ MarketPriceRecord objects.
        """

        raise NotImplementedError(
            "Each market source adapter must implement fetch()."
        )

    def normalize(
        self,
        record: dict,
    ) -> MarketPriceRecord:
        """
        Convert a source-specific dictionary into the common
        FarmIQ MarketPriceRecord format.
        """

        if "market_id" not in record:
            raise ValueError("market_id is required.")

        if "crop_id" not in record:
            raise ValueError("crop_id is required.")

        if "price" not in record:
            raise ValueError("price is required.")

        if "price_date" not in record:
            raise ValueError("price_date is required.")

        if "currency" not in record:
            raise ValueError("currency is required.")

        if "unit" not in record:
            raise ValueError("unit is required.")

        price_date = self._normalize_date(
            record["price_date"]
        )

        price = self._normalize_decimal(
            record["price"],
            "price",
        )

        min_price = self._normalize_optional_decimal(
            record.get("min_price"),
            "min_price",
        )

        max_price = self._normalize_optional_decimal(
            record.get("max_price"),
            "max_price",
        )

        source = record.get(
            "source",
            self.source_name,
        )

        return MarketPriceRecord(
            market_id=int(record["market_id"]),
            crop_id=int(record["crop_id"]),
            price=price,
            price_date=price_date,
            currency=str(
                record["currency"]
            ).strip().upper(),
            unit=str(
                record["unit"]
            ).strip().upper(),
            source=str(source).strip(),
            source_reference=record.get(
                "source_reference"
            ),
            min_price=min_price,
            max_price=max_price,
            quality_grade=record.get(
                "quality_grade"
            ),
            notes=record.get(
                "notes"
            ),
        )

    # --------------------------------------------------------
    # Helpers
    # --------------------------------------------------------

    @staticmethod
    def _normalize_date(value) -> datetime:
        """
        Normalize date/datetime/string into datetime.
        """

        if isinstance(value, datetime):
            return value

        if isinstance(value, date):
            return datetime(
                value.year,
                value.month,
                value.day,
            )

        if isinstance(value, str):

            value = value.strip()

            if not value:
                raise ValueError(
                    "price_date cannot be empty."
                )

            try:
                return datetime.fromisoformat(
                    value
                )
            except ValueError:
                pass

            try:
                return datetime.strptime(
                    value,
                    "%Y-%m-%d",
                )
            except ValueError:
                raise ValueError(
                    "Invalid price_date. "
                    "Use YYYY-MM-DD or ISO datetime."
                )

        raise ValueError(
            "price_date must be a date, datetime, "
            "or ISO date/datetime string."
        )

    @staticmethod
    def _normalize_decimal(
        value,
        field_name: str,
    ) -> Decimal:
        """
        Convert numeric values into Decimal.
        """

        try:
            result = Decimal(str(value))
        except Exception:
            raise ValueError(
                f"{field_name} must be numeric."
            )

        if result <= 0:
            raise ValueError(
                f"{field_name} must be greater than zero."
            )

        return result

    @staticmethod
    def _normalize_optional_decimal(
        value,
        field_name: str,
    ) -> Optional[Decimal]:
        """
        Convert optional numeric values into Decimal.
        """

        if value is None:
            return None

        try:
            result = Decimal(str(value))
        except Exception:
            raise ValueError(
                f"{field_name} must be numeric."
            )

        if result < 0:
            raise ValueError(
                f"{field_name} cannot be negative."
            )

        return result


# ============================================================
# MANUAL / FARM IQ SOURCE
# ============================================================

class FarmIQSourceAdapter(MarketSourceAdapter):
    """
    Adapter for prices entered directly through FarmIQ.

    This is useful for:
        - market officers
        - administrators
        - cooperative reports
        - farmer reports
        - manual verification
    """

    source_name = "FARM_IQ"

    def fetch(
        self,
        records: list[dict],
    ) -> list[MarketPriceRecord]:
        """
        Normalize manually supplied records.
        """

        normalized_records = []

        for record in records:

            normalized = self.normalize(record)

            normalized_records.append(
                normalized
            )

        return normalized_records


# ============================================================
# TEST SOURCE ADAPTER
# ============================================================

class TestMarketSourceAdapter(MarketSourceAdapter):
    """
    Development adapter used to verify the source architecture.

    This adapter does NOT represent real market data.
    """

    source_name = "TEST_SOURCE"

    def fetch(
        self,
        market_id: int,
        crop_id: int,
    ) -> list[MarketPriceRecord]:
        """
        Return a small deterministic test dataset.
        """

        records = [
            {
                "market_id": market_id,
                "crop_id": crop_id,
                "price": "490",
                "price_date": "2026-09-19",
                "currency": "RWF",
                "unit": "KG",
                "source": self.source_name,
                "source_reference": (
                    "FarmIQ source adapter architecture test"
                ),
                "min_price": "470",
                "max_price": "510",
                "quality_grade": "STANDARD",
            },
            {
                "market_id": market_id,
                "crop_id": crop_id,
                "price": "495",
                "price_date": "2026-09-20",
                "currency": "RWF",
                "unit": "KG",
                "source": self.source_name,
                "source_reference": (
                    "FarmIQ source adapter architecture test"
                ),
                "min_price": "475",
                "max_price": "515",
                "quality_grade": "STANDARD",
            },
        ]

        return [
            self.normalize(record)
            for record in records
        ]


# ============================================================
# SOURCE REGISTRY
# ============================================================

class MarketSourceRegistry:
    """
    Registry for FarmIQ market-data adapters.

    Centralizes available sources so the application can
    discover and use adapters without hard-coding them.
    """

    def __init__(self):
        self._adapters: dict[
            str,
            MarketSourceAdapter,
        ] = {}

    def register(
        self,
        adapter: MarketSourceAdapter,
    ) -> None:
        """
        Register a market source adapter.
        """

        if not isinstance(
            adapter,
            MarketSourceAdapter,
        ):
            raise TypeError(
                "adapter must inherit from "
                "MarketSourceAdapter."
            )

        source_name = adapter.source_name.strip().upper()

        if not source_name:
            raise ValueError(
                "Adapter source_name cannot be empty."
            )

        self._adapters[source_name] = adapter

    def get(
        self,
        source_name: str,
    ) -> MarketSourceAdapter:
        """
        Retrieve a registered adapter.
        """

        key = source_name.strip().upper()

        adapter = self._adapters.get(key)

        if adapter is None:
            raise ValueError(
                f"No market source adapter registered "
                f"for '{source_name}'."
            )

        return adapter

    def list_sources(self) -> list[str]:
        """
        Return registered source names.
        """

        return sorted(
            self._adapters.keys()
        )


# ============================================================
# DEFAULT REGISTRY
# ============================================================

def create_default_market_source_registry():
    """
    Create FarmIQ's default source registry.

    Currently:
        FARM_IQ
        TEST_SOURCE

    Real FAO/EAX adapters will be added separately.
    """

    registry = MarketSourceRegistry()

    registry.register(
        FarmIQSourceAdapter()
    )

    registry.register(
        TestMarketSourceAdapter()
    )

    return registry
