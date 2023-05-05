from datetime import datetime, date
from typing import List

import pytest
from fastapi import HTTPException
from pydantic import BaseModel
from pydantic_sqlalchemy import sqlalchemy_to_pydantic
from starlette.status import HTTP_400_BAD_REQUEST

from tests.conftest import Vacancy
from tests.utils import JobCategory

PydanticVacancy = sqlalchemy_to_pydantic(Vacancy)


class ListPydanticVacancy(BaseModel):
    vacancies: List[PydanticVacancy] = []


async def test_eq_with_int(session, get_filter, create_vacancies):
    query = get_filter.get_or_query("salary_from__eq=60")
    res = await session.execute(query)
    data = PydanticVacancy.from_orm(res.scalar()).dict()
    assert isinstance(data["created_at"], date)
    assert isinstance(data["updated_at"], datetime)
    check_data = data.copy()
    del check_data["created_at"]
    del check_data["updated_at"]
    assert check_data == {
        'id': 1,
        'title': 'title1',
        'description': 'description1',
        'is_active': True,
        'salary_from': 60,
        'salary_up_to': 110,
        'category': JobCategory.miscellaneous
    }


async def test_in_with_str(session, get_filter, create_vacancies):
    query = get_filter.get_or_query("description__in_=[description1, description2]")
    res = await session.execute(query)
    data = ListPydanticVacancy(vacancies=res.scalars().all()).dict()
    assert len(data['vacancies']) == 2
    assert isinstance(data['vacancies'][0]["created_at"], date)
    assert isinstance(data['vacancies'][0]["updated_at"], datetime)
    check_data = data['vacancies'][0].copy()
    del check_data['created_at']
    del check_data['updated_at']
    assert check_data == {
        'id': 1,
        'title': 'title1',
        'description': 'description1',
        'is_active': True,
        'salary_from': 60,
        'salary_up_to': 110,
        'category': JobCategory.miscellaneous
    }


async def test_in_with_int(session, get_filter, create_vacancies):
    query = get_filter.get_or_query("salary_from__in_=[60, 70, 80]")
    res = await session.execute(query)
    data = ListPydanticVacancy(vacancies=res.scalars().all()).dict()
    assert len(data['vacancies']) == 3
    assert isinstance(data['vacancies'][0]["created_at"], date)
    assert isinstance(data['vacancies'][0]["updated_at"], datetime)
    check_data = data['vacancies'][0].copy()
    del check_data['created_at']
    del check_data['updated_at']
    assert check_data == {
        'id': 1,
        'title': 'title1',
        'description': 'description1',
        'is_active': True,
        'salary_from': 60,
        'salary_up_to': 110,
        'category': JobCategory.miscellaneous
    }


async def test_between_with_int(session, get_filter, create_vacancies):
    query = get_filter.get_or_query("salary_from__between=[50, 90]")
    res = await session.execute(query)
    data = ListPydanticVacancy(vacancies=res.scalars().all()).dict()
    assert len(data['vacancies']) == 4
    assert isinstance(data['vacancies'][0]["created_at"], date)
    assert isinstance(data['vacancies'][0]["updated_at"], datetime)
    check_data = data['vacancies'][0].copy()
    del check_data['created_at']
    del check_data['updated_at']
    assert check_data == {
        'id': 1,
        'title': 'title1',
        'description': 'description1',
        'is_active': True,
        'salary_from': 60,
        'salary_up_to': 110,
        'category': JobCategory.miscellaneous
    }


# async def test_between_with_date(session, get_filter, create_vacancies):
#     query = get_filter.get_or_query("created_at__between=[50, 90]")
#     res = await session.execute(query)
#     data = ListPydanticVacancy(vacancies=res.scalars().all()).dict()


async def test_qt_with_int(session, get_filter, create_vacancies):
    query = get_filter.get_or_query("salary_from__gt=100")
    res = await session.execute(query)
    data = ListPydanticVacancy(vacancies=res.scalars().all()).dict()
    assert len(data['vacancies']) == 5
    assert isinstance(data['vacancies'][0]["created_at"], date)
    assert isinstance(data['vacancies'][0]["updated_at"], datetime)
    check_data = data['vacancies'][0].copy()
    del check_data['created_at']
    del check_data['updated_at']
    assert check_data == {
        'id': 6,
        'title': 'title6',
        'description': 'description6',
        'is_active': True,
        'salary_from': 110,
        'salary_up_to': 160,
        'category': JobCategory.miscellaneous
    }


@pytest.mark.parametrize(
    "bad_filter, expected_status_code, expected_detail",
    (
        (
            "salary_from__qt=100",
            HTTP_400_BAD_REQUEST,
            "Forbidden filter 'qt' for 'salary_from'"
         ),
        (
            "id__gt=100",
            HTTP_400_BAD_REQUEST,
            "Forbidden filter field 'id'"
         ),
        (
            "salary_from__eq=",
            HTTP_400_BAD_REQUEST,
            [
                {
                    'loc': ['salary_from'],
                    'msg': 'value is not a valid integer',
                    'type': 'type_error.integer'
                }
            ]
        ),
        (
            "salary__eq=100",
            HTTP_400_BAD_REQUEST,
            "DB model <class 'conftest.Vacancy'> doesn't have field 'salary'"
        ),
        (
            "salary_from_eq=100",
            HTTP_400_BAD_REQUEST,
            "Incorrect filter request syntax, "
            "please use pattern :'field_name__operand=value'"
        ),
        (
            "salary_from__eq-100",
            HTTP_400_BAD_REQUEST,
            "Incorrect filter request syntax, "
            "please use pattern :'field_name__operand=value'"
        )
    )
)
def test_fail_filter_operand(get_filter, bad_filter, expected_status_code, expected_detail):
    try:
        get_filter.get_or_query(bad_filter)
    except HTTPException as e:
        assert e.status_code == expected_status_code
        assert e.detail == expected_detail


# data = ListPydanticVacancy(vacancies=res.scalars().all()).dict()
# "description__eq=description1"
