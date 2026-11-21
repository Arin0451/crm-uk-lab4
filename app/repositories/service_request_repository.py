from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import RequestStatus, ServiceRequest


class ServiceRequestRepository:
    """Выполняет операции с заявками внутри переданной сессии."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, *, resident_id: int, subject: str, description: str) -> ServiceRequest:
        request = ServiceRequest(
            resident_id=resident_id, subject=subject, description=description
        )
        self.session.add(request)
        self.session.flush()
        return request

    def get(self, request_id: int) -> ServiceRequest | None:
        return self.session.get(ServiceRequest, request_id)

    def list(self, *, status: RequestStatus | None = None) -> list[ServiceRequest]:
        query = select(ServiceRequest).order_by(ServiceRequest.id)
        if status is not None:
            query = query.where(ServiceRequest.status == status)
        return list(self.session.scalars(query))

    def update(
        self,
        request_id: int,
        *,
        status: RequestStatus,
        category: str | None,
        assignee_id: int | None,
    ) -> ServiceRequest | None:
        request = self.get(request_id)
        if request is None:
            return None
        request.status = status
        request.category = category
        request.assignee_id = assignee_id
        self.session.flush()
        self.session.expire(request, ["assignee"])
        return request

    def delete(self, request_id: int) -> bool:
        request = self.get(request_id)
        if request is None:
            return False
        self.session.delete(request)
        self.session.flush()
        return True
