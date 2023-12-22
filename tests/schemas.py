from typing import List

from pydantic import ConfigDict, BaseModel
from sqlalchemy_to_pydantic import sqlalchemy_to_pydantic

from tests.conftest import Vacancy
from tests.utils import JobCategory

PydanticVacancy = sqlalchemy_to_pydantic(Vacancy)


class CustomPydanticVacancy(BaseModel):
    id: int
    is_active: bool
    sum_salary_from: float
    category: JobCategory

    model_config = ConfigDict(from_attributes=True)


class ListPydanticVacancy(BaseModel):
    vacancies: List[PydanticVacancy] = []


class ListCustomPydanticVacancy(BaseModel):
    vacancies: List[CustomPydanticVacancy] = []
