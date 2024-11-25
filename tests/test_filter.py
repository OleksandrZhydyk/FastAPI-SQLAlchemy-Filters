from datetime import datetime, date

import pytest
from fastapi import HTTPException
from starlette.status import HTTP_400_BAD_REQUEST
from tests.utils import JobCategory
from tests.schemas import ListPydanticVacancy, ListCustomPydanticVacancy


async def test_empty_query(session, get_vacancy_filter, create_vacancies):
    query = get_vacancy_filter.get_query("")
    res = await session.execute(query)
    data = ListPydanticVacancy(
        vacancies=res.scalars().all()
    ).model_dump(exclude={"created_at", "updated_at", "company_id"})

    assert len(data["vacancies"]) == 10
    assert isinstance(data["vacancies"][0]["created_at"], date)
    assert isinstance(data["vacancies"][0]["updated_at"], datetime)
    check_data = data["vacancies"][0].copy()
    del check_data["created_at"]
    del check_data["updated_at"]
    del check_data["company_id"]
    assert check_data == {
        "id": 1,
        "title": "title1",
        "description": "description1",
        "is_active": True,
        "salary_from": 60,
        "salary_up_to": 110.725,
        "category": JobCategory.finance
    }


async def test_eq_with_int(session, get_vacancy_filter, create_vacancies):
    query = get_vacancy_filter.get_query("salary_from__eq=60")
    res = await session.execute(query)
    data = ListPydanticVacancy(
        vacancies=res.scalars().all()
    ).model_dump(exclude={"created_at", "updated_at", "company_id"})

    assert len(data["vacancies"]) == 1
    assert isinstance(data["vacancies"][0]["created_at"], date)
    assert isinstance(data["vacancies"][0]["updated_at"], datetime)
    check_data = data["vacancies"][0].copy()
    del check_data["created_at"]
    del check_data["updated_at"]
    del check_data["company_id"]
    assert check_data == {
        "id": 1,
        "title": "title1",
        "description": "description1",
        "is_active": True,
        "salary_from": 60,
        "salary_up_to": 110.725,
        "category": JobCategory.finance
    }


async def test_eq_with_float(session, get_vacancy_filter, create_vacancies):
    query = get_vacancy_filter.get_query("salary_up_to__eq=120.725")
    res = await session.execute(query)
    data = ListPydanticVacancy(
        vacancies=res.scalars().all()
    ).model_dump(exclude={"created_at", "updated_at", "company_id"})

    assert len(data["vacancies"]) == 1
    assert isinstance(data["vacancies"][0]["created_at"], date)
    assert isinstance(data["vacancies"][0]["updated_at"], datetime)
    check_data = data["vacancies"][0].copy()
    del check_data["created_at"]
    del check_data["updated_at"]
    del check_data["company_id"]
    assert check_data == {
        "id": 2,
        "title": "title2",
        "description": "description2",
        "is_active": False,
        "salary_from": 70,
        "salary_up_to": 120.725,
        "category": JobCategory.marketing
    }


async def test_in_with_str(session, get_vacancy_filter, create_vacancies):
    query = get_vacancy_filter.get_query("description__in_=description1,description2")
    res = await session.execute(query)
    data = ListPydanticVacancy(vacancies=res.scalars().all()).model_dump()
    assert len(data["vacancies"]) == 2
    assert isinstance(data["vacancies"][0]["created_at"], date)
    assert isinstance(data["vacancies"][0]["updated_at"], datetime)
    check_data = data["vacancies"][0].copy()
    del check_data["created_at"]
    del check_data["updated_at"]
    del check_data["company_id"]
    assert check_data == {
        "id": 1,
        "title": "title1",
        "description": "description1",
        "is_active": True,
        "salary_from": 60,
        "salary_up_to": 110.725,
        "category": JobCategory.finance
    }


async def test_contains_with_str(session, get_vacancy_filter, create_vacancies):
    query = get_vacancy_filter.get_query("description__contains=tion1")
    res = await session.execute(query)
    data = ListPydanticVacancy(vacancies=res.scalars().all()).model_dump()
    assert len(data["vacancies"]) == 2
    assert isinstance(data["vacancies"][0]["created_at"], date)
    assert isinstance(data["vacancies"][0]["updated_at"], datetime)
    check_data = data["vacancies"][-1].copy()
    del check_data["created_at"]
    del check_data["updated_at"]
    del check_data["company_id"]
    assert check_data == {
        "id": 10,
        "title": "title10",
        "description": "description10",
        "is_active": False,
        "salary_from": 150,
        "salary_up_to": 200.725,
        "category": JobCategory.miscellaneous
    }


async def test_endswith_with_str(session, get_vacancy_filter, create_vacancies):
    query = get_vacancy_filter.get_query("title__endswith=le1")
    res = await session.execute(query)
    data = ListPydanticVacancy(vacancies=res.scalars().all()).model_dump()
    assert len(data["vacancies"]) == 1
    assert isinstance(data["vacancies"][0]["created_at"], date)
    assert isinstance(data["vacancies"][0]["updated_at"], datetime)
    check_data = data["vacancies"][0].copy()
    del check_data["created_at"]
    del check_data["updated_at"]
    del check_data["company_id"]
    assert check_data == {
        "id": 1,
        "title": "title1",
        "description": "description1",
        "is_active": True,
        "salary_from": 60,
        "salary_up_to": 110.725,
        "category": JobCategory.finance
    }


async def test_in_with_int(session, get_vacancy_filter, create_vacancies):
    query = get_vacancy_filter.get_query("salary_from__in_=60,70,80")
    res = await session.execute(query)
    data = ListPydanticVacancy(vacancies=res.scalars().all()).model_dump()
    assert len(data["vacancies"]) == 3
    assert isinstance(data["vacancies"][0]["created_at"], date)
    assert isinstance(data["vacancies"][0]["updated_at"], datetime)
    check_data = data["vacancies"][0].copy()
    del check_data["created_at"]
    del check_data["updated_at"]
    del check_data["company_id"]
    assert check_data == {
        "id": 1,
        "title": "title1",
        "description": "description1",
        "is_active": True,
        "salary_from": 60,
        "salary_up_to": 110.725,
        "category": JobCategory.finance
    }


async def test_gte_with_int(session, get_vacancy_filter, create_vacancies):
    query = get_vacancy_filter.get_query("salary_from__gte=120")
    res = await session.execute(query)
    data = ListPydanticVacancy(vacancies=res.scalars().all()).model_dump()
    assert len(data["vacancies"]) == 4
    assert isinstance(data["vacancies"][0]["created_at"], date)
    assert isinstance(data["vacancies"][0]["updated_at"], datetime)
    check_data = data["vacancies"][0].copy()
    del check_data["created_at"]
    del check_data["updated_at"]
    del check_data["company_id"]
    assert check_data == {
        "id": 7,
        "title": "title7",
        "description": "description7",
        "is_active": True,
        "salary_from": 120,
        "salary_up_to": 170.725,
        "category": JobCategory.construction
    }


async def test_not_eq_with_date(session, get_vacancy_filter, create_vacancies):
    query = get_vacancy_filter.get_query("created_at__not_eq=2023-05-01")
    res = await session.execute(query)
    data = ListPydanticVacancy(vacancies=res.scalars().all()).model_dump()
    assert len(data["vacancies"]) == 9
    assert isinstance(data["vacancies"][0]["created_at"], date)
    assert isinstance(data["vacancies"][0]["updated_at"], datetime)
    check_data = data["vacancies"][0].copy()
    del check_data["created_at"]
    del check_data["updated_at"]
    del check_data["company_id"]
    assert check_data == {
        "id": 2,
        "title": "title2",
        "description": "description2",
        "is_active": False,
        "salary_from": 70,
        "salary_up_to": 120.725,
        "category": JobCategory.marketing
    }


async def test_eq_with_bool(session, get_vacancy_filter, create_vacancies):
    query = get_vacancy_filter.get_query("is_active__eq=true")
    res = await session.execute(query)
    data = ListPydanticVacancy(vacancies=res.scalars().all()).model_dump()
    assert len(data["vacancies"]) == 5
    assert isinstance(data["vacancies"][0]["created_at"], date)
    assert isinstance(data["vacancies"][0]["updated_at"], datetime)
    check_data = data["vacancies"][0].copy()
    del check_data["created_at"]
    del check_data["updated_at"]
    del check_data["company_id"]
    assert check_data == {
        "id": 1,
        "title": "title1",
        "description": "description1",
        "is_active": True,
        "salary_from": 60,
        "salary_up_to": 110.725,
        "category": JobCategory.finance
    }


async def test_between_with_int(session, get_vacancy_filter, create_vacancies):
    query = get_vacancy_filter.get_query("salary_from__between=50,90")
    res = await session.execute(query)
    data = ListPydanticVacancy(vacancies=res.scalars().all()).model_dump()
    assert len(data["vacancies"]) == 4
    assert isinstance(data["vacancies"][0]["created_at"], date)
    assert isinstance(data["vacancies"][0]["updated_at"], datetime)
    check_data = data["vacancies"][0].copy()
    del check_data["created_at"]
    del check_data["updated_at"]
    del check_data["company_id"]
    assert check_data == {
        "id": 1,
        "title": "title1",
        "description": "description1",
        "is_active": True,
        "salary_from": 60,
        "salary_up_to": 110.725,
        "category": JobCategory.finance
    }


async def test_between_with_datetime(session, get_vacancy_filter, create_vacancies):
    query = get_vacancy_filter.get_query("updated_at__between=2023-01-01 00:00:00,2023-05-01 00:00:00")
    res = await session.execute(query)
    data = ListPydanticVacancy(vacancies=res.scalars().all()).model_dump()
    assert len(data["vacancies"]) == 4
    assert isinstance(data["vacancies"][0]["created_at"], date)
    assert isinstance(data["vacancies"][0]["updated_at"], datetime)
    check_data = data["vacancies"][-1].copy()
    del check_data["created_at"]
    del check_data["updated_at"]
    del check_data["company_id"]
    assert check_data == {
        "id": 4,
        "title": "title4",
        "description": "description4",
        "is_active": False,
        "salary_from": 90,
        "salary_up_to": 140.725,
        "category": JobCategory.it
    }


async def test_between_with_date(session, get_vacancy_filter, create_vacancies):
    query = get_vacancy_filter.get_query("created_at__between=2023-05-01,2023-05-05")
    res = await session.execute(query)
    data = ListPydanticVacancy(vacancies=res.scalars().all()).model_dump()
    assert len(data["vacancies"]) == 5
    assert isinstance(data["vacancies"][0]["created_at"], date)
    assert isinstance(data["vacancies"][0]["updated_at"], datetime)
    check_data = data["vacancies"][-1].copy()
    del check_data["created_at"]
    del check_data["updated_at"]
    del check_data["company_id"]
    assert check_data == {
        "id": 5,
        "title": "title5",
        "description": "description5",
        "is_active": True,
        "salary_from": 100,
        "salary_up_to": 150.725,
        "category": JobCategory.metallurgy
    }


async def test_gt_with_int(session, get_vacancy_filter, create_vacancies):
    query = get_vacancy_filter.get_query("salary_from__gt=100")
    res = await session.execute(query)
    data = ListPydanticVacancy(vacancies=res.scalars().all()).model_dump()
    assert len(data["vacancies"]) == 5
    assert isinstance(data["vacancies"][0]["created_at"], date)
    assert isinstance(data["vacancies"][0]["updated_at"], datetime)
    check_data = data["vacancies"][0].copy()
    del check_data["created_at"]
    del check_data["updated_at"]
    del check_data["company_id"]
    assert check_data == {
        "id": 6,
        "title": "title6",
        "description": "description6",
        "is_active": False,
        "salary_from": 110,
        "salary_up_to": 160.725,
        "category": JobCategory.medicine
    }


async def test_enum_with_str(session, get_vacancy_filter, create_vacancies):
    query = get_vacancy_filter.get_query("category__eq=Medicine")
    res = await session.execute(query)
    data = ListPydanticVacancy(vacancies=res.scalars().all()).model_dump()
    assert len(data["vacancies"]) == 1
    assert isinstance(data["vacancies"][0]["created_at"], date)
    assert isinstance(data["vacancies"][0]["updated_at"], datetime)
    check_data = data["vacancies"][0].copy()
    del check_data["created_at"]
    del check_data["updated_at"]
    del check_data["company_id"]
    assert check_data == {
        "id": 6,
        "title": "title6",
        "description": "description6",
        "is_active": False,
        "salary_from": 110,
        "salary_up_to": 160.725,
        "category": JobCategory.medicine
    }


async def test_complex_query(session, get_vacancy_filter, create_vacancies):
    query = get_vacancy_filter.get_query(
        "created_at__between=2023-05-01,2023-05-05&"
        "updated_at__in_=2023-01-05 15:15:15,2023-05-05 15:15:15|"
        "salary_from__gt=100"
    )
    res = await session.execute(query)
    data = ListPydanticVacancy(vacancies=res.scalars().all()).model_dump()
    assert len(data["vacancies"]) == 7
    assert isinstance(data["vacancies"][0]["created_at"], date)
    assert isinstance(data["vacancies"][0]["updated_at"], datetime)
    check_data = data["vacancies"][1].copy()
    del check_data["created_at"]
    del check_data["updated_at"]
    del check_data["company_id"]
    assert check_data == {
        "id": 5,
        "title": "title5",
        "description": "description5",
        "is_active": True,
        "salary_from": 100,
        "salary_up_to": 150.725,
        "category": JobCategory.metallurgy
    }


async def test_complex_query_with_order_by(session, get_vacancy_filter, create_vacancies):
    query = get_vacancy_filter.get_query(
        "created_at__between=2023-05-01,2023-05-05&"
        "updated_at__in_=2023-01-05 15:15:15,2023-05-05 15:15:15|"
        "salary_from__gt=100&"
        "order_by=-id"
    )
    res = await session.execute(query)
    data = ListPydanticVacancy(vacancies=res.scalars().all()).model_dump()
    assert len(data["vacancies"]) == 7
    assert isinstance(data["vacancies"][0]["created_at"], date)
    assert isinstance(data["vacancies"][0]["updated_at"], datetime)
    check_data = data["vacancies"][0].copy()
    del check_data["created_at"]
    del check_data["updated_at"]
    del check_data["company_id"]
    assert check_data == {
        "id": 10,
        "title": "title10",
        "description": "description10",
        "is_active": False,
        "salary_from": 150,
        "salary_up_to": 200.725,
        "category": JobCategory.miscellaneous
    }


async def test_order_by_id(session, get_vacancy_filter, create_vacancies):
    query = get_vacancy_filter.get_query("order_by=-id")
    res = await session.execute(query)
    data = ListPydanticVacancy(vacancies=res.scalars().all()).model_dump()
    assert len(data["vacancies"]) == 10
    assert isinstance(data["vacancies"][0]["created_at"], date)
    assert isinstance(data["vacancies"][0]["updated_at"], datetime)
    check_data = data["vacancies"][0].copy()
    del check_data["created_at"]
    del check_data["updated_at"]
    del check_data["company_id"]
    assert check_data == {
        "id": 10,
        "title": "title10",
        "description": "description10",
        "is_active": False,
        "salary_from": 150,
        "salary_up_to": 200.725,
        "category": JobCategory.miscellaneous
    }


async def test_custom_query(session, get_custom_vacancy_filter, create_vacancies):
    query = get_custom_vacancy_filter.get_query("")
    res = await session.execute(query)
    data = ListCustomPydanticVacancy(vacancies=res.all()).model_dump(exclude_none=True)
    assert len(data["vacancies"]) == 2
    check_data = data["vacancies"][0].copy()
    assert check_data == {
        "id": 2,
        "is_active": False,
        "sum_salary_from": 550,
        "category": JobCategory.marketing
    }


async def test_custom_complex_query(session, get_custom_vacancy_filter, create_vacancies):
    query = get_custom_vacancy_filter.get_query(
        "created_at__between=2023-05-01,2023-05-05&"
        "updated_at__in_=2023-01-05 15:15:15,2023-05-05 15:15:15|"
        "salary_from__gt=100&"
        "order_by=-salary_from"
    )
    res = await session.execute(query)
    data = ListCustomPydanticVacancy(vacancies=res.all()).model_dump(exclude_none=True)
    assert len(data["vacancies"]) == 2
    check_data = data["vacancies"][0].copy()
    assert check_data == {
        "id": 6,
        "is_active": False,
        "sum_salary_from": 390,
        "category": JobCategory.medicine
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
                    "type": "int_parsing",
                    "loc": ["salary_from"],
                    "msg": "Input should be a valid integer, unable to parse string as an integer",
                    "input": ""
                }
            ]
        ),
        (
            "salary__eq=100",
            HTTP_400_BAD_REQUEST,
            "DB model Vacancy doesn't have field 'salary'"
        ),
        (
            "salary_from_eq=100",
            HTTP_400_BAD_REQUEST,
            "Incorrect filter request syntax, "
            "please use pattern :'{field_name}__{condition}={value}{conjunction}' "
            "or '{relation}.{field_name}__{condition}={value}{conjunction}'"
        ),
        (
            "salary_from__eq-100",
            HTTP_400_BAD_REQUEST,
            "Incorrect filter request syntax, "
            "please use pattern :'{field_name}__{condition}={value}{conjunction}' "
            "or '{relation}.{field_name}__{condition}={value}{conjunction}'"
        ),
        (
            "category__eq=Unknown_category",
            HTTP_400_BAD_REQUEST,
            [
                {
                    "type": "enum",
                    "loc": ["category"],
                    "msg": "Input should be 'Finance', 'Marketing', 'Agriculture', 'IT', "
                           "'Metallurgy', 'Medicine', 'Construction', 'Building', 'Services' or 'Miscellaneous'",
                    "input": "Unknown_category",
                    "ctx": {
                        "expected": "'Finance', 'Marketing', 'Agriculture', 'IT', 'Metallurgy', 'Medicine', "
                                    "'Construction', 'Building', 'Services' or 'Miscellaneous'"
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
            "please use pattern :'{field_name}__{condition}={value}{conjunction}' "
            "or '{relation}.{field_name}__{condition}={value}{conjunction}'"
        ),
        (
            "is_active__eq=100",
            HTTP_400_BAD_REQUEST,
            [
                {
                    "type": "bool_parsing",
                    "loc": ["is_active"],
                    "msg": "Input should be a valid boolean, unable to interpret input",
                    "input": "100"
                }
            ]
        ),
        (
            "salary_up_to__eq=100/12",
            HTTP_400_BAD_REQUEST,
            [
                {
                    "type": "float_parsing",
                    "loc": ["salary_up_to"],
                    "msg": "Input should be a valid number, unable to parse string as a number",
                    "input": "100/12"
                }
            ]
        ),
    )
)
def test_fail_filter(get_vacancy_filter, bad_filter, expected_status_code, expected_detail):
    with pytest.raises(HTTPException) as e:
        get_vacancy_filter.get_query(bad_filter)
    assert e.type == HTTPException
    assert e.value.status_code == expected_status_code

    errors_details = e.value.detail

    if isinstance(errors_details, list):
        for detail in errors_details:
            detail.pop("url")

    assert errors_details == expected_detail


async def test_relation_search(session, get_custom_company_filter, create_vacancies):
    query = get_custom_company_filter.get_query("title__eq=MyCompany2&vacancies.salary_from__gte=100")
    res = await session.execute(query)
    companies = res.unique().scalars().all()

    assert len(companies) == 1
    assert len(companies[0].vacancies) == 6

    company = companies[0]
    assert company.id == 2
    assert company.title == "MyCompany2"


@pytest.mark.parametrize(
    "bad_filter, expected_status_code, expected_detail",
    (
        (
            "unknown.vacancies.salary_from__gte=100",
            HTTP_400_BAD_REQUEST,
            "Incorrect filter request syntax, "
            "please use pattern :'{field_name}__{condition}={value}{conjunction}' "
            "or '{relation}.{field_name}__{condition}={value}{conjunction}'"
        ),
        (
            "unknown.salary_from__gte=100",
            HTTP_400_BAD_REQUEST,
            "Can not find relation unknown in Company model"
        ),
    )
)
def test_fail_relation_filter(get_custom_company_filter, bad_filter, expected_status_code, expected_detail):
    with pytest.raises(HTTPException) as e:
        get_custom_company_filter.get_query(bad_filter)
    assert e.type == HTTPException
    assert e.value.status_code == expected_status_code

    errors_details = e.value.detail

    if isinstance(errors_details, list):
        for detail in errors_details:
            detail.pop("url")

    assert errors_details == expected_detail
