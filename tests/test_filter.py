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
    query = get_filter.get_query("salary_from__eq=60")
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
        'category': JobCategory.finance
    }


async def test_in_with_str(session, get_filter, create_vacancies):
    query = get_filter.get_query("description__in_=description1,description2")
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
        'category': JobCategory.finance
    }


async def test_contains_with_str(session, get_filter, create_vacancies):
    query = get_filter.get_query("description__contains=tion1")
    res = await session.execute(query)
    data = ListPydanticVacancy(vacancies=res.scalars().all()).dict()
    assert len(data['vacancies']) == 2
    assert isinstance(data['vacancies'][0]["created_at"], date)
    assert isinstance(data['vacancies'][0]["updated_at"], datetime)
    check_data = data['vacancies'][-1].copy()
    del check_data['created_at']
    del check_data['updated_at']
    assert check_data == {
        'id': 10,
        'title': 'title10',
        'description': 'description10',
        'is_active': True,
        'salary_from': 150,
        'salary_up_to': 200,
        'category': JobCategory.miscellaneous
    }


async def test_in_with_int(session, get_filter, create_vacancies):
    query = get_filter.get_query("salary_from__in_=60,70,80")
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
        'category': JobCategory.finance
    }


async def test_between_with_int(session, get_filter, create_vacancies):
    query = get_filter.get_query("salary_from__between=50,90")
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
        'category': JobCategory.finance
    }


async def test_between_with_datetime(session, get_filter, create_vacancies):
    query = get_filter.get_query("updated_at__between=2023-01-01 0:0:0,2023-05-01 0:0:0")
    res = await session.execute(query)
    data = ListPydanticVacancy(vacancies=res.scalars().all()).dict()
    assert len(data['vacancies']) == 4
    assert isinstance(data['vacancies'][0]["created_at"], date)
    assert isinstance(data['vacancies'][0]["updated_at"], datetime)
    check_data = data['vacancies'][-1].copy()
    del check_data['created_at']
    del check_data['updated_at']
    assert check_data == {
        'id': 4,
        'title': 'title4',
        'description': 'description4',
        'is_active': True,
        'salary_from': 90,
        'salary_up_to': 140,
        'category': JobCategory.it
    }


async def test_between_with_date(session, get_filter, create_vacancies):
    query = get_filter.get_query("created_at__between=2023-05-01,2023-05-05")
    res = await session.execute(query)
    data = ListPydanticVacancy(vacancies=res.scalars().all()).dict()
    assert len(data['vacancies']) == 5
    assert isinstance(data['vacancies'][0]["created_at"], date)
    assert isinstance(data['vacancies'][0]["updated_at"], datetime)
    check_data = data['vacancies'][-1].copy()
    del check_data['created_at']
    del check_data['updated_at']
    assert check_data == {
        'id': 5,
        'title': 'title5',
        'description': 'description5',
        'is_active': True,
        'salary_from': 100,
        'salary_up_to': 150,
        'category': JobCategory.metallurgy
    }


async def test_qt_with_int(session, get_filter, create_vacancies):
    query = get_filter.get_query("salary_from__gt=100")
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
        'category': JobCategory.medicine
    }


async def test_enum_with_str(session, get_filter, create_vacancies):
    query = get_filter.get_query("category__eq=Medicine")
    res = await session.execute(query)
    data = ListPydanticVacancy(vacancies=res.scalars().all()).dict()
    assert len(data['vacancies']) == 1
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
        'category': JobCategory.medicine
    }


async def test_complex_query(session, get_filter, create_vacancies):
    query = get_filter.get_query(
        "created_at__between=2023-05-01,2023-05-05&"
        "updated_at__in_=2023-01-05 15:15:15,2023-05-05 15:15:15|"
        "salary_from__gt=100"
    )
    res = await session.execute(query)
    data = ListPydanticVacancy(vacancies=res.scalars().all()).dict()
    assert len(data['vacancies']) == 7
    assert isinstance(data['vacancies'][0]["created_at"], date)
    assert isinstance(data['vacancies'][0]["updated_at"], datetime)
    check_data = data['vacancies'][1].copy()
    del check_data['created_at']
    del check_data['updated_at']
    assert check_data == {
        'id': 5,
        'title': 'title5',
        'description': 'description5',
        'is_active': True,
        'salary_from': 100,
        'salary_up_to': 150,
        'category': JobCategory.metallurgy
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
            "please use pattern :'{field_name}__{condition}={value}{conjunction}'"
        ),
        (
            "salary_from__eq-100",
            HTTP_400_BAD_REQUEST,
            "Incorrect filter request syntax, "
            "please use pattern :'{field_name}__{condition}={value}{conjunction}'"
        ),
        (
            "category__eq=Unknown_category",
            HTTP_400_BAD_REQUEST,
            [
                {
                    'loc': ['category'],
                    'msg': "value is not a valid enumeration member; "
                           "permitted: 'Finance', 'Marketing', 'Agriculture', 'IT', 'Metallurgy', 'Medicine', "
                           "'Construction', 'Building', 'Services', 'Miscellaneous'",
                    'type': 'type_error.enum',
                    'ctx':
                        {
                            'enum_values':
                                [
                                    'Finance', 'Marketing', 'Agriculture', 'IT', 'Metallurgy', 'Medicine',
                                    'Construction', 'Building', 'Services', 'Miscellaneous'
                                ]
                    }
                }
            ]
        ),
        (
            "created_at__between=2023-05-01,2023-05-05"
            "updated_at__in_=2023-01-05 15:15:15,2023-05-05 15:15:15|"
            "salary_from__gt=100",
            HTTP_400_BAD_REQUEST,
            "Incorrect filter request syntax, "
            "please use pattern :'{field_name}__{condition}={value}{conjunction}'"
        )
    )
)
def test_fail_filter(get_filter, bad_filter, expected_status_code, expected_detail):
    with pytest.raises(Exception) as e:
        get_filter.get_query(bad_filter)
    assert e.type == HTTPException
    assert e.value.status_code == expected_status_code
    assert e.value.detail == expected_detail
