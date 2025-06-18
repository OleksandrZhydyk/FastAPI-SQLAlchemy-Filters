import pytest
from fastapi import HTTPException
from starlette.status import HTTP_400_BAD_REQUEST


async def test_relation_search(session, get_custom_company_filter, create_vacancies):
    query = get_custom_company_filter.get_query("title__eq=MyCompany2&vacancies.salary_from__gte=100")
    res = await session.execute(query)
    companies = res.unique().scalars().all()

    assert len(companies) == 1
    assert len(companies[0].vacancies) == 6

    company = companies[0]
    assert company.id == 2
    assert company.title == "MyCompany2"


async def test_pass_custom_select_into_init(session, get_filter_passed_in_init, create_vacancies):
    query = get_filter_passed_in_init.get_query("title__eq=MyCompany2&vacancies.salary_from__gte=100")
    res = await session.execute(query)
    companies = res.unique().scalars().all()

    assert len(companies) == 1

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


async def test_reverse_relation(session, get_vacancy_filter_with_join, create_vacancies):
    query = get_vacancy_filter_with_join.get_query("company.title__eq=MyCompany1")
    res = await session.execute(query)
    vacancies = res.unique().scalars().all()

    assert len(vacancies) == 4
    vacancy = vacancies[0]
    assert vacancy.id == 1
    assert vacancy.company_id == 1


async def test_relation_mixed_search(session, get_custom_company_filter, create_vacancies):
    query = get_custom_company_filter.get_query("title__eq=MyCompany2&vacancies.salary_from__gte=100&id__eq=2")
    res = await session.execute(query)
    companies = res.unique().scalars().all()

    assert len(companies) == 1
    assert len(companies[0].vacancies) == 6

    company = companies[0]
    assert company.id == 2
    assert company.title == "MyCompany2"
