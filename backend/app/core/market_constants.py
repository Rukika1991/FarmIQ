# ============================================================
# FARM-IQ MARKET CONSTANTS
# ============================================================
#
# Central definitions for FarmIQ Market Intelligence.
#
# Market levels:
#   LOCAL
#   NATIONAL
#   REGIONAL
#   INTERNATIONAL
#
# Market types:
#   FARM_GATE
#   WHOLESALE
#   RETAIL
#   EXPORT
#   COMMODITY_EXCHANGE
#   OTHER
#
# ============================================================


# ============================================================
# MARKET LEVELS
# ============================================================

MARKET_LEVEL_LOCAL = "LOCAL"

MARKET_LEVEL_NATIONAL = "NATIONAL"

MARKET_LEVEL_REGIONAL = "REGIONAL"

MARKET_LEVEL_INTERNATIONAL = "INTERNATIONAL"


# ============================================================
# MARKET TYPES
# ============================================================

MARKET_TYPE_FARM_GATE = "FARM_GATE"

MARKET_TYPE_WHOLESALE = "WHOLESALE"

MARKET_TYPE_RETAIL = "RETAIL"

MARKET_TYPE_EXPORT = "EXPORT"

MARKET_TYPE_COMMODITY_EXCHANGE = "COMMODITY_EXCHANGE"

MARKET_TYPE_OTHER = "OTHER"


# ============================================================
# SUPPORTED MARKET LEVELS
# ============================================================

MARKET_LEVELS = {
    MARKET_LEVEL_LOCAL,
    MARKET_LEVEL_NATIONAL,
    MARKET_LEVEL_REGIONAL,
    MARKET_LEVEL_INTERNATIONAL,
}


# ============================================================
# SUPPORTED MARKET TYPES
# ============================================================

MARKET_TYPES = {
    MARKET_TYPE_FARM_GATE,
    MARKET_TYPE_WHOLESALE,
    MARKET_TYPE_RETAIL,
    MARKET_TYPE_EXPORT,
    MARKET_TYPE_COMMODITY_EXCHANGE,
    MARKET_TYPE_OTHER,
}


# ============================================================
# DISPLAY NAMES
# ============================================================
#
# These are useful for the future FarmIQ frontend/dashboard.
# Database values remain the standardized uppercase values above.
# ============================================================

MARKET_LEVEL_DISPLAY_NAMES = {
    MARKET_LEVEL_LOCAL: "Local Market",
    MARKET_LEVEL_NATIONAL: "National Market",
    MARKET_LEVEL_REGIONAL: "Regional Market",
    MARKET_LEVEL_INTERNATIONAL: "International Market",
}


MARKET_TYPE_DISPLAY_NAMES = {
    MARKET_TYPE_FARM_GATE: "Farm Gate",
    MARKET_TYPE_WHOLESALE: "Wholesale",
    MARKET_TYPE_RETAIL: "Retail",
    MARKET_TYPE_EXPORT: "Export",
    MARKET_TYPE_COMMODITY_EXCHANGE: "Commodity Exchange",
    MARKET_TYPE_OTHER: "Other",
}


# ============================================================
# VALIDATION HELPERS
# ============================================================

def is_valid_market_level(value: str) -> bool:
    """
    Check whether a market level is supported by FarmIQ.
    """

    if not value:
        return False

    return value.upper() in MARKET_LEVELS


def is_valid_market_type(value: str) -> bool:
    """
    Check whether a market type is supported by FarmIQ.
    """

    if not value:
        return False

    return value.upper() in MARKET_TYPES


def normalize_market_level(value: str) -> str:
    """
    Normalize a market level to the FarmIQ standard.

    Examples:
        local       -> LOCAL
        National    -> NATIONAL
        regional    -> REGIONAL
    """

    if not value:
        raise ValueError(
            "Market level cannot be empty."
        )

    normalized = value.strip().upper()

    if normalized not in MARKET_LEVELS:
        raise ValueError(
            f"Invalid market level: {value}. "
            f"Supported values: "
            f"{', '.join(sorted(MARKET_LEVELS))}"
        )

    return normalized


def normalize_market_type(value: str) -> str:
    """
    Normalize a market type to the FarmIQ standard.

    Examples:
        farm_gate   -> FARM_GATE
        Wholesale   -> WHOLESALE
        retail      -> RETAIL
    """

    if not value:
        raise ValueError(
            "Market type cannot be empty."
        )

    normalized = value.strip().upper()

    if normalized not in MARKET_TYPES:
        raise ValueError(
            f"Invalid market type: {value}. "
            f"Supported values: "
            f"{', '.join(sorted(MARKET_TYPES))}"
        )

    return normalized
