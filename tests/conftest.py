import asyncio
from datetime import date, datetime

import pytest
import pytest_asyncio
from sqlalchemy import Column, Integer, Date, Text, String, Boolean, DateTime, Enum, Float, select, or_, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

from fastapi_sa_orm_filter.main import FilterCore
from fastapi_sa_orm_filter.operators import Operators as ops
from tests.utils import JobCategory

Base = declarative_base()


class Vacancy(Base):
    __tablename__ = "vacancies"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(Date)
    updated_at = Column(DateTime)
    salary_from = Column(Integer)
    salary_up_to = Column(Float)
    category = Column(Enum(JobCategory), nullable=False)


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
    return sessionmaker(create_engine, expire_on_commit=False, class_=AsyncSession)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


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
        def __init__(self, model, allowed_filters):
            super().__init__(model, allowed_filters)

        def get_unordered_query(self, conditions):
            unordered_query = select(
                self._model.id,
                self._model.is_active,
                func.sum(self._model.salary_from).label("salary_from"),
                self._model.category
            ).filter(or_(*conditions)).group_by(self._model.is_active)
            return unordered_query

    return CustomFilter(Vacancy, get_custom_restriction)
