from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class DiseaseDetection(Base):
    __tablename__ = "disease_detections"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    # Farm context
    field_id: Mapped[int] = mapped_column(
        ForeignKey("fields.id"),
        nullable=False,
        index=True,
    )

    crop_id: Mapped[int] = mapped_column(
        ForeignKey("crops.id"),
        nullable=False,
        index=True,
    )

    # Uploaded image
    image_path: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Detection information
    detected_disease: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    confidence: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 4),
        nullable=True,
    )

    severity: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    symptoms: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    treatment: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    prevention: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    recommendation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # AI model information
    model_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    model_version: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    # Detection lifecycle
    status: Mapped[str] = mapped_column(
        String(30),
        default="PENDING",
        nullable=False,
        index=True,
    )

    detected_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    field: Mapped["Field"] = relationship()

    crop: Mapped["Crop"] = relationship()
