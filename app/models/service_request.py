from datetime import datetime
from enum import Enum

from sqlalchemy import CheckConstraint, Enum as SQLEnum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.employee import Employee
from app.models.resident import Resident


class RequestStatus(str, Enum):
    ACCEPTED = "accepted"
    ASSIGNED = "assigned"
    SUSPENDED = "suspended"
    CLOSED = "closed"


class ServiceRequest(Base):
    __tablename__ = "service_requests"
    __table_args__ = (
        CheckConstraint(
            "status NOT IN ('assigned', 'closed') OR assignee_id IS NOT NULL",
            name="ck_service_requests_assignee_required",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    resident_id: Mapped[int] = mapped_column(
        ForeignKey("residents.id", ondelete="RESTRICT"), index=True
    )
    assignee_id: Mapped[int | None] = mapped_column(
        ForeignKey("employees.id", ondelete="RESTRICT"), index=True
    )
    subject: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(80))
    status: Mapped[RequestStatus] = mapped_column(
        SQLEnum(
            RequestStatus,
            values_callable=lambda statuses: [status.value for status in statuses],
            name="ck_service_requests_status",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
        ),
        server_default=RequestStatus.ACCEPTED.value,
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.current_timestamp())

    resident: Mapped[Resident] = relationship()
    assignee: Mapped[Employee | None] = relationship()
