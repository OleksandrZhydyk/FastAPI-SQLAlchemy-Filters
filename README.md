## FastAPI SQLAlchemy Filter 
![ci_badge](https://github.com/OleksandrZhydyk/FastAPI-SQLAlchemy-Filters/actions/workflows/ci_filter.yml/badge.svg)
[![Downloads](https://static.pepy.tech/badge/fastapi_sa_orm_filter)](https://pepy.tech/project/fastapi_sa_orm_filter)
[![PyPI version](https://img.shields.io/pypi/v/fastapi-sa-orm-filter.svg)](https://pypi.org/project/fastapi-sa-orm-filter/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Package that helps to implement easy objects filtering and sorting for applications
build on FastAPI and SQLAlchemy.
For using you just need to define your custom filter with filtered fields and applied operators.
Supported operators, datatypes and example of work you can find below.

### Installation
```shell
pip install fastapi-sa-orm-filter
```
### Compatibility
v 0.2.1
 - Python: >= 3.10
 - Fastapi: >= 0.100
 - Pydantic: >= 2.0.0
 - SQLAlchemy: >= 1.4.36, < 2.1.0

v 0.1.5
 - Python: >= 3.8
 - Fastapi: <= 0.100
 - Pydantic: < 2.0.0
 - SQLAlchemy: == 1.4

### Quickstart

```shell
from fastapi import FastAPI
from fastapi.params import Query
from fastapi_sa_orm_filter.main import FilterCore
from fastapi_sa_orm_filter.operators import Operators as ops

from db.base import get_session
from db.models import MyModel


app = FastAPI()

# Define fields and operators for filter
my_objects_filter = {
    'my_model_field_name': [ops.eq, ops.in_],
    'my_model_field_name': [ops.between, ops.eq, ops.gt, ops.lt, ops.in_],
    'my_model_field_name': [ops.like, ops.startswith, ops.contains, ops.in_],
    'my_model_field_name': [ops.between, ops.not_eq, ops.gte, ops.lte]
}

@app.get("/")
async def get_filtered_objects(
    filter_query: str = Query(default=''),
    db: AsyncSession = Depends(get_session)
 ) -> List[MyModel]:
    my_filter = FilterCore(MyModel, my_objects_filter)
    query = my_filter.get_query(filter_query)
    res = await db.execute(query)
    return res.scalars().all()
```

### Examples of usage

```shell

# Input query string
'''
salary_from__in_=60,70,80&
created_at__between=2023-05-01,2023-05-05|
category__eq=Medicine&
order_by=-id,category
'''

   
# Returned SQLAlchemy orm query exact as:
           
select(model)
    .where(
        or_(
            and_(
                model.salary_from.in_(60,70,80),
                model.created_at.between(2023-05-01, 2023-05-05)
            ),
            model.category == 'Medicine'
        ).order_by(model.id.desc(), model.category.asc())
```

```shell
# Filter by joined model

# Input query string
'''vacancies.salary_from__gte=100'''

allowed_filter_fields = {
    "id": [ops.eq],
    "title": [ops.startswith, ops.eq, ops.contains],
    "salary_from": [ops.eq, ops.gt, ops.lte, ops.gte]
}

company_filter = FilterCore(
    Company, 
    allowed_filter_fields, 
    select(Company).join(Vacancy).options(joinedload(Company.vacancies))
)

@app.get("/")
async def get_filtered_company(
    filter_query: str = "title__eq=MyCompany&vacancies.salary_from__gte=100",
    db: AsyncSession = Depends(get_session)
 ) -> List[Company]:
  
    query = company_filter.get_query(filter_query)
    res = await db.execute(query)
    return res.scalars().all()
    
# Returned SQLAlchemy query
select(Company)
  .join(Vacancy)
  .options(joinedload(Company.vacancies))
  .where(
    and_(
      Company.title == "MyCompany", 
      Vacancy.salary_from >= 100
    )
  )

```

### Supported query string format

* field_name__eq=value
* field_name__in_=value1,value2
* field_name__eq=value&field_name__in_=value1,value2
* field_name__eq=value&field_name__in_=value1,value2&order_by=-field_name

### Modify query for custom selection
```shell
# Create a class inherited from FilterCore and rewrite 'get_unordered_query' method.
# ^0.2.0 Version

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


# 0.1.5 Version
# Original method is:
def get_unordered_query(self, conditions):
    unordered_query = select(self._model).filter(or_(*conditions))
    return unordered_query
    
# Rewrite example:
class CustomFilter(FilterCore):

    def get_unordered_query(self, conditions):
        unordered_query = select(
            self.model.field_name1,
            self.model.field_name2,
            func.sum(self.model.field_name3).label("field_name3"),
            self.model.field_name4
        ).filter(or_(*conditions)).group_by(self.model.field_name2)
        return unordered_query

```

### Supported SQLAlchemy datatypes:
* DATETIME
* DATE
* INTEGER
* FLOAT
* TEXT
* VARCHAR
* Enum(VARCHAR())
* BOOLEAN

### Available filter operators:
* __eq__
* __gt__
* __lt__
* __gte__
* __lte__
* __in___
* __startswith__
* __endswith__
* __between__
* __like__
* __ilike__
* __contains__
* __icontains__
* __not_eq__
* __not_in__
* __not_like__
* __not_between__
