from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from alembic import command
from alembic.config import Config
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import create_db_engine
from app.models import Employee, RequestStatus, Resident
from app.repositories import ServiceRequestRepository


class ServiceRequestRepositoryTest(TestCase):
    def setUp(self) -> None:
        temp_dir = TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        database_env = patch.dict(
            "os.environ", {"CRM_DB_PATH": str(Path(temp_dir.name) / "test.db")}
        )
        database_env.start()
        self.addCleanup(database_env.stop)
        command.upgrade(Config("alembic.ini"), "head")
        self.engine = create_db_engine()
        self.addCleanup(self.engine.dispose)

        with Session(self.engine) as session, session.begin():
            resident = Resident(full_name="Тестовый житель", address="Учебная улица, дом 1")
            employee = Employee(full_name="Тестовый сотрудник", role="Сантехник")
            session.add_all([resident, employee])
            session.flush()
            self.resident_id = resident.id
            self.employee_id = employee.id

    def test_crud_and_status_filter(self) -> None:
        with Session(self.engine) as session, session.begin():
            repository = ServiceRequestRepository(session)
            request = repository.create(
                resident_id=self.resident_id,
                subject="Протечка",
                description="Требуется осмотр трубы",
            )
            request_id = request.id
            self.assertEqual(request.status, RequestStatus.ACCEPTED)
            self.assertIsNotNone(request.created_at)

        with Session(self.engine) as session, session.begin():
            repository = ServiceRequestRepository(session)
            request = repository.get(request_id)
            self.assertEqual(request.subject, "Протечка")
            self.assertIsNone(request.assignee)
            updated = repository.update(
                request_id,
                status=RequestStatus.ASSIGNED,
                category="Сантехника",
                assignee_id=self.employee_id,
            )
            self.assertEqual(updated.assignee.id, self.employee_id)
            self.assertEqual(
                [item.id for item in repository.list(status=RequestStatus.ASSIGNED)],
                [request_id],
            )
            self.assertEqual(repository.list(status=RequestStatus.ACCEPTED), [])

        with Session(self.engine) as session, session.begin():
            repository = ServiceRequestRepository(session)
            self.assertEqual(repository.get(request_id).category, "Сантехника")
            self.assertTrue(repository.delete(request_id))

        with Session(self.engine) as session:
            self.assertIsNone(ServiceRequestRepository(session).get(request_id))

    def test_missing_request(self) -> None:
        with Session(self.engine) as session:
            repository = ServiceRequestRepository(session)
            self.assertIsNone(repository.get(1))
            self.assertIsNone(
                repository.update(
                    1, status=RequestStatus.SUSPENDED, category=None, assignee_id=None
                )
            )
            self.assertFalse(repository.delete(1))

    def test_rejects_unknown_resident(self) -> None:
        with Session(self.engine) as session:
            repository = ServiceRequestRepository(session)
            with self.assertRaises(IntegrityError), session.begin():
                repository.create(
                    resident_id=self.resident_id + 1,
                    subject="Заявка без жильца",
                    description="Проверка внешнего ключа",
                )
            self.assertEqual(repository.list(), [])

    def test_rejects_assignment_without_employee(self) -> None:
        with Session(self.engine) as session:
            repository = ServiceRequestRepository(session)
            with session.begin():
                request = repository.create(
                    resident_id=self.resident_id, subject="Протечка", description="Осмотр"
                )
                request_id = request.id

            with self.assertRaises(IntegrityError), session.begin():
                repository.update(
                    request_id,
                    status=RequestStatus.ASSIGNED,
                    category="Сантехника",
                    assignee_id=None,
                )
            self.assertEqual(repository.get(request_id).status, RequestStatus.ACCEPTED)
