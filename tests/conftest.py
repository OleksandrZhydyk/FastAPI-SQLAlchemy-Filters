from datetime import date, datetime

import pytest
import pytest_asyncio
from pytest_asyncio import is_async_test

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from fastapi_sa_orm_filter.main import FilterCore
from fastapi_sa_orm_filter.operators import Operators as ops
from tests.utils import JobCategory

Base = declarative_base()


class Vacancy(Base):
    __tablename__ = "vacancies"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    description: Mapped[str]
    is_active: Mapped[bool]
    created_at: Mapped[date]
    updated_at: Mapped[datetime]
    salary_from: Mapped[int]
    salary_up_to: Mapped[float]
    category: Mapped[JobCategory] = mapped_column(nullable=False)


def pytest_collection_modifyitems(items):
    pytest_asyncio_tests = (item for item in items if is_async_test(item))
    session_scope_marker = pytest.mark.asyncio(scope="session")
    for async_test in pytest_asyncio_tests:
        async_test.add_marker(session_scope_marker)


@pytest.fixture(scope="session")
def sqlite_file_path(tmp_path_factory):
    file_path = tmp_path_factory.mktemp("data")
    yield file_path


@pytest.fixture(scope="session")
def database_url(sqlite_file_path) -> str:
    return f"sqlite+aiosqlite:///{sqlite_file_path}.db"


@pytest.fixture(scope="session")
def create_engine(database_url):
    return create_async_engine(database_url, echo=True, future=True)


@pytest.fixture(scope="session")
def create_session(create_engine):
    return async_sessionmaker(create_engine, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True, scope="function")
async def db_models(create_engine):
    async with create_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with create_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def session(create_session) -> AsyncSession:
    async with create_session() as session:
        yield session


@pytest.fixture(scope="function")
async def create_vacancies(session):
    vacancy_instances = []
    enum_category = [member.name for member in JobCategory]
    for i in range(1, 11):
        vacancy = Vacancy(
            title=f"title{i}",
            description=f"description{i}",
            salary_from=50 + i * 10,
            salary_up_to=100.725 + i * 10,
            created_at=date(2023, 5, i),
            updated_at=datetime(2023, i, 5, 15, 15, 15),
            category=JobCategory[enum_category[i - 1]],
            is_active=bool(i % 2)
        )
        vacancy_instances.append(vacancy)
    session.add_all(vacancy_instances)
    await session.commit()


@pytest.fixture
def get_custom_restriction():
    return {
        'title': [ops.startswith, ops.eq, ops.endswith],
        'category': [ops.startswith, ops.eq, ops.in_],
        'salary_from': [ops.between, ops.eq, ops.gt, ops.lt, ops.in_, ops.gte],
        'salary_up_to': [ops.eq, ops.gt],
        'description': [ops.like, ops.not_like, ops.contains, ops.eq, ops.in_],
        'created_at': [ops.between, ops.in_, ops.eq, ops.gt, ops.lt, ops.not_eq],
        'updated_at': [ops.between, ops.in_, ops.eq, ops.gt, ops.lt],
        'is_active': [ops.eq]
    }


@pytest.fixture
def get_filter(get_custom_restriction):
    return FilterCore(Vacancy, get_custom_restriction)


@pytest.fixture
def get_custom_filter(get_custom_restriction):

    class CustomFilter(FilterCore):

        def get_select_query_part(self):
            custom_select = select(
                self.model.id,
                self.model.is_active,
                func.sum(self.model.salary_from).label("sum_salary_from"),
                self.model.category
            )
            return custom_select

        def get_group_by_query_part(self):
            return [self.model.is_active]

    return CustomFilter(Vacancy, get_custom_restriction)
