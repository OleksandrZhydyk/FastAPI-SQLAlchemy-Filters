import asyncio
from datetime import date, datetime

import pytest
import pytest_asyncio
from sqlalchemy import Column, Integer, Date, Text, String, Boolean, DateTime, Enum
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

from base_filters.main import FilterCore
from base_filters.filters import FiltersList as fls
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
    salary_up_to = Column(Integer)
    category = Column(Enum(JobCategory), nullable=False)


def database_url(sqlite_file_path) -> str:
    return f"sqlite+aiosqlite:///{sqlite_file_path}"

engine = create_async_engine(database_url('test.db'), echo=True, future=True)

async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True, scope="function")
async def db_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def session() -> AsyncSession:
    async with async_session() as session:
        yield session


@pytest.fixture(scope="function")
async def create_vacancies(session):
    vacancy_instances = []
    for i in range(1, 11):
        vacancy = Vacancy(
            title=f"title{i}",
            description=f"description{i}",
            salary_from=50 + i*10,
            salary_up_to=100 + i*10,
            created_at=date(2023, 5, 5+i),
            updated_at=datetime(2023, 1+i, 5, 15, 15, 15),
            category=JobCategory.miscellaneous
        )
        vacancy_instances.append(vacancy)
    session.add_all(vacancy_instances)
    await session.commit()

@pytest.fixture
def get_custom_restriction():
    return {
        'title': [fls.startswith, fls.eq, fls.in_],
        'category': [fls.startswith, fls.eq, fls.in_],
        'salary_from': [fls.between, fls.eq, fls.gt, fls.lt, fls.in_],
        'description': [fls.like, fls.not_like, fls.contains, fls.eq, fls.in_],
        'created_at': [fls.between, fls.like, fls.in_, fls.contains, fls.eq, fls.gt, fls.lt]
    }


@pytest.fixture
def get_filter(get_custom_restriction):
    return FilterCore(Vacancy, get_custom_restriction)
