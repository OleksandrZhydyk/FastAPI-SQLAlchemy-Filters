from datetime import datetime, date
from typing import List

from pydantic import BaseModel
from pydantic_sqlalchemy import sqlalchemy_to_pydantic

from tests.conftest import Vacancy
from tests.utils import JobCategory

PydanticVacancy = sqlalchemy_to_pydantic(Vacancy)


class ListPydanticVacancy(BaseModel):
    vacancies: List[PydanticVacancy] = []


async def get_vacancy_by_description(session, get_filter, create_vacancies):
    query = get_filter.get_or_query("description__eq=description1")
    res = await session.execute(query)
    data = PydanticVacancy.from_orm(res.scalar()).dict()
    assert isinstance(data["created_at"], date)
    assert isinstance(data["updated_at"], datetime)
    check_data = data.copy()
    del check_data["created_at"]
    del check_data["updated_at"]
    assert check_data == {
        'id': 2,
        'title': 'title1',
        'description': 'description1',
        'is_active': True,
        'salary_from': 60,
        'salary_up_to': 110,
        'category': JobCategory.miscellaneous
    }


# data = ListPydanticVacancy(vacancies=res.scalars().all()).dict()
# "description__eq=description1"