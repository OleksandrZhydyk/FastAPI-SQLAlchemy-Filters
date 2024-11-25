from datetime import date, datetime

import pytest
import pytest_asyncio

from sqlalchemy import select, func, ForeignKey
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, relationship, joinedload
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
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    company: Mapped["Company"] = relationship(back_populates="vacancies")


class Company(Base):
    __tablename__ = "companies"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    vacancies: Mapped[list["Vacancy"]] = relationship(back_populates="company")


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


@pytest.fixture
async def create_companies(session):
    companies = []
    for i in range(1, 3):
        company_instance = Company(title=f"MyCompany{i}")
        session.add(company_instance)
        await session.commit()
        await session.refresh(company_instance)
        companies.append(company_instance)
    return companies


@pytest.fixture(scope="function")
async def create_vacancies(session, create_companies):
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
            is_active=bool(i % 2),
            company=create_companies[(50 + i * 10)//100]
        )
        vacancy_instances.append(vacancy)
    session.add_all(vacancy_instances)
    await session.commit()


@pytest.fixture
def get_vacancy_restriction() -> dict:
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
def get_vacancy_filter(get_vacancy_restriction):
    return FilterCore(Vacancy, get_vacancy_restriction)


@pytest.fixture
def get_custom_vacancy_filter(get_vacancy_restriction):

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

    return CustomFilter(Vacancy, get_vacancy_restriction)


@pytest.fixture
def get_company_restriction() -> dict:
    return {
        "id": [ops.eq],
        "title": [ops.startswith, ops.eq, ops.contains],
        "salary_from": [ops.eq, ops.gt, ops.lte, ops.gte]
    }


@pytest.fixture
def get_company_filter(get_company_restriction):
    return FilterCore(Company, get_company_restriction)


@pytest.fixture
def get_custom_company_filter(get_company_restriction):

    class CustomFilter(FilterCore):
        def get_query(self, custom_filter):
            query = super().get_query(custom_filter)
            return query.join(Vacancy).options(joinedload(Company.vacancies))

    return CustomFilter(Company, get_company_restriction)
