from datetime import datetime
from decimal import Decimal
from typing import Optional

import httpx

from app.services.market_sources import (
    MarketPriceRecord,
    MarketSourceAdapter,
)


class FAOProducerPriceAdapter(MarketSourceAdapter):
    """
    Adapter for FAOSTAT Agricultural Producer Prices.

    IMPORTANT:
        FAOSTAT Producer Prices represent producer/farm-gate
        prices and should NOT be treated as wholesale or retail
        market prices.

    The adapter is deliberately separated from the FPMA adapter
    that we will build later for domestic wholesale/retail prices.
    """

    source_name = "FAOSTAT_PRODUCER_PRICE"

    DEFAULT_TIMEOUT = 30.0

    def __init__(
        self,
        api_base_url: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        self.api_base_url = api_base_url
        self.timeout = timeout

    # ============================================================
    # NORMALIZE ONE FAO RECORD
    # ============================================================

    def normalize_fao_record(
        self,
        record: dict,
        market_id: int,
        crop_id: int,
    ) -> MarketPriceRecord:
        """
        Convert a FAOSTAT producer-price record into the
        FarmIQ normalized MarketPriceRecord.

        Expected FAO fields may vary slightly between API
        versions, therefore the adapter accepts common aliases.
        """

        price = self._first_value(
            record,
            [
                "Value",
                "value",
                "Price",
                "price",
            ],
        )

        if price is None:
            raise ValueError(
                "FAO record does not contain a price/value."
            )

        price_date = self._extract_date(record)

        currency = self._first_value(
            record,
            [
                "Currency",
                "currency",
            ],
        )

        if not currency:
            currency = "USD"

        unit = self._first_value(
            record,
            [
                "Unit",
                "unit",
            ],
        )

        if not unit:
            unit = "KG"

        source_reference = self._first_value(
            record,
            [
                "Source",
                "source",
                "SourceReference",
                "source_reference",
            ],
        )

        item_name = self._first_value(
            record,
            [
                "Item",
                "item",
                "ItemDescription",
                "item_description",
            ],
        )

        area_name = self._first_value(
            record,
            [
                "Area",
                "area",
                "AreaName",
                "area_name",
            ],
        )

        notes_parts = [
            "FAOSTAT agricultural producer price",
            "farm-gate / first-point-of-sale price",
        ]

        if item_name:
            notes_parts.append(
                f"Item: {item_name}"
            )

        if area_name:
            notes_parts.append(
                f"Area: {area_name}"
            )

        return MarketPriceRecord(
            market_id=market_id,
            crop_id=crop_id,
            price=self._normalize_decimal(
                price,
                "FAO price",
            ),
            price_date=price_date,
            currency=str(currency).strip().upper(),
            unit=self._normalize_unit(unit),
            source=self.source_name,
            source_reference=source_reference,
            notes="; ".join(notes_parts),
        )

    # ============================================================
    # NORMALIZE A LIST
    # ============================================================

    def normalize_fao_records(
        self,
        records: list[dict],
        market_id: int,
        crop_id: int,
    ) -> list[MarketPriceRecord]:
        """
        Normalize multiple FAOSTAT records.
        """

        normalized = []

        for record in records:
            normalized.append(
                self.normalize_fao_record(
                    record=record,
                    market_id=market_id,
                    crop_id=crop_id,
                )
            )

        return normalized

    # ============================================================
    # API FETCH
    # ============================================================

    def fetch(
        self,
        url: Optional[str] = None,
        params: Optional[dict] = None,
        market_id: Optional[int] = None,
        crop_id: Optional[int] = None,
    ) -> list[MarketPriceRecord]:
        """
        Fetch FAOSTAT data from a supplied API endpoint.

        We intentionally require the verified API URL rather
        than hard-coding an unverified endpoint.

        This protects FarmIQ from silently depending on an
        outdated FAOSTAT endpoint.
        """

        if not url and not self.api_base_url:
            raise ValueError(
                "A verified FAOSTAT API URL is required."
            )

        if market_id is None:
            raise ValueError(
                "market_id is required."
            )

        if crop_id is None:
            raise ValueError(
                "crop_id is required."
            )

        request_url = (
            url
            if url
            else self.api_base_url
        )

        try:
            with httpx.Client(
                timeout=self.timeout
            ) as client:

                response = client.get(
                    request_url,
                    params=params or {},
                )

                response.raise_for_status()

                payload = response.json()

        except httpx.HTTPError as exc:
            raise RuntimeError(
                f"FAOSTAT request failed: {exc}"
            ) from exc

        records = self._extract_records(
            payload
        )

        return self.normalize_fao_records(
            records=records,
            market_id=market_id,
            crop_id=crop_id,
        )

    # ============================================================
    # PAYLOAD HANDLING
    # ============================================================

    @staticmethod
    def _extract_records(payload) -> list[dict]:
        """
        Extract records from common API response structures.
        """

        if isinstance(payload, list):
            return payload

        if not isinstance(payload, dict):
            raise ValueError(
                "Unexpected FAOSTAT API response format."
            )

        for key in (
            "data",
            "Data",
            "records",
            "Records",
            "results",
            "Results",
        ):
            value = payload.get(key)

            if isinstance(value, list):
                return value

        raise ValueError(
            "Could not find market-price records "
            "in FAOSTAT response."
        )

    # ============================================================
    # DATE HANDLING
    # ============================================================

    @staticmethod
    def _extract_date(record: dict) -> datetime:
        """
        Extract a date from common FAOSTAT field names.
        """

        value = None

        for key in (
            "Year",
            "year",
            "Date",
            "date",
            "Period",
            "period",
        ):
            if key in record:
                value = record[key]
                break

        if value is None:
            raise ValueError(
                "FAO record does not contain a date/year."
            )

        if isinstance(value, datetime):
            return value

        if isinstance(value, int):
            return datetime(
                int(value),
                1,
                1,
            )

        value = str(value).strip()

        # YYYY
        if len(value) == 4 and value.isdigit():
            return datetime(
                int(value),
                1,
                1,
            )

        # ISO datetime
        try:
            return datetime.fromisoformat(
                value
            )
        except ValueError:
            pass

        # ISO date
        try:
            return datetime.strptime(
                value,
                "%Y-%m-%d",
            )
        except ValueError:
            raise ValueError(
                f"Unable to parse FAO date: {value}"
            )

    # ============================================================
    # HELPERS
    # ============================================================

    @staticmethod
    def _first_value(
        record: dict,
        keys: list[str],
    ):
        for key in keys:
            if key in record:
                value = record[key]

                if value is not None:
                    return value

        return None

    @staticmethod
    def _normalize_decimal(
        value,
        field_name: str,
    ) -> Decimal:
        try:
            result = Decimal(str(value))
        except Exception as exc:
            raise ValueError(
                f"{field_name} must be numeric."
            ) from exc

        if result <= 0:
            raise ValueError(
                f"{field_name} must be greater than zero."
            )

        return result

    @staticmethod
    def _normalize_unit(
        unit: str,
    ) -> str:
        """
        Normalize common FAO units to FarmIQ units.
        """

        normalized = str(unit).strip().upper()

        mapping = {
            "KG": "KG",
            "1000 T": "TONNE",
            "T": "TONNE",
            "TON": "TONNE",
            "TONNE": "TONNE",
            "TONNES": "TONNE",
            "MT": "TONNE",
            "USD/KG": "KG",
            "RWF/KG": "KG",
        }

        return mapping.get(
            normalized,
            normalized,
        )
