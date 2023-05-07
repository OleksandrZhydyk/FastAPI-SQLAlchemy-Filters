## FastAPI SQLAlchemy Filter 
Package that helps to implement easy objects filter for applications
build on FastAPI and SQLAlchemy.
For using you just need to define your custom filter with filtered fields and applied operators.
Supported operators, datatypes and example of work you can find below.

### Installation
```shell
pip install fastapi-sa-orm-filter
```

### Quickstart

```shell
from fastapi import FastAPI
from fastapi.params import Query
from fastapi_sa_orm_filter.main import FilterCore
from fastapi_sa_orm_filter.filters import FiltersList as fls

from db.base import get_session
from db.models import MyModel


app = FastAPI()

# Define fields and operators for filter
my_item_filter = {
    'my_model_field_name': [fls.eq, fls.in_],
    'my_model_field_name': [fls.between, fls.eq, fls.gt, fls.lt, fls.in_],
    'my_model_field_name': [fls.like, fls.startswith, fls.contains, fls.in_],
    'my_model_field_name': [fls.between, fls.not_eq, fls.gte, fls.lte]
}

@app.get("/")
async def get_filtered_items(
    filter: str = Query(default=''),
    db: AsyncSession = Depends(get_session)
 ) -> List[MyModel]:
    my_filter = FilterCore(MyModel, my_item_filter)
    query = my_filter.get_query(filter)
    res = await db.execute(query)
    return res.scalars().all()
```

### Example of work

```shell

# Input query string
'''
    salary_from__in_=60,70,80&
    created_at__between=2023-05-01,2023-05-05|
    category__eq=Medicine"
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
        )
```

### Supported query string format

* field_name__eq=value
* field_name__in_=value1,value2
* field_name__eq=value&field_name__in_=value1,value2

### Supported SQLAlchemy datatypes:
* DATETIME
* DATE
* INTEGER
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
