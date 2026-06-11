from __future__ import annotations

import uuid
from enum import Enum as PyEnum

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Integer, String, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.models.base import AuditMixin, Base


class RuleType(str, PyEnum):
    WORKING_HOURS = "working_hours"
    HOLIDAY = "holiday"
    MAINTENANCE = "maintenance"
    BLACKOUT = "blackout"
    CUSTOM = "custom"


class AvailabilityRuleModel(AuditMixin, Base):
    __tablename__ = "availability_rules"
    __table_args__ = {"schema": "public"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("public.tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    resource_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("public.resources.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    rule_type: Mapped[str] = mapped_column(
        Enum(RuleType, name="rule_type_enum", values_callable=lambda x: [e.value for e in x], create_type=False), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # For recurring weekly rules
    weekday: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 0=Mon, 6=Sun
    start_time: Mapped[object | None] = mapped_column(Time, nullable=True)
    end_time: Mapped[object | None] = mapped_column(Time, nullable=True)
    # For date-specific rules
    specific_date: Mapped[object | None] = mapped_column(Date, nullable=True)
    # For date-range rules
    date_from: Mapped[object | None] = mapped_column(Date, nullable=True)
    date_to: Mapped[object | None] = mapped_column(Date, nullable=True)
    is_recurring: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    resource: Mapped["ResourceModel"] = relationship(  # type: ignore[name-defined]
        "ResourceModel", back_populates="availability_rules", lazy="noload"
    )
