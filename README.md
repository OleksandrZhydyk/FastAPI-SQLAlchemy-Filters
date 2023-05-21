## FastAPI SQLAlchemy Filter 
Package that helps to implement easy objects filtering and sorting for applications
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

### Example of work

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

### Supported query string format

* field_name__eq=value
* field_name__in_=value1,value2
* field_name__eq=value&field_name__in_=value1,value2
* field_name__eq=value&field_name__in_=value1,value2&order_by=-field_name

### Modify query for custom selection
```shell
# Create a class inherited from FilterCore and rewrite 'get_unordered_query' method.
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

#### For suggestions and questions, feel free to contact me through email 
__zhydykalex@ukr.net__

