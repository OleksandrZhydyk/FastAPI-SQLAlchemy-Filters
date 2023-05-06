## FastAPI SQLAlchemy Filter 

### Supported query string format

* field_name__eq=value
* field_name__in_=value1,value2
* field_name__eq=value&field_name__in_=value1,value2

### Quickstart

```shell
from fastapi import FastAPI
from fastapi.params import Query
from fastapi_sqlalchemy_filter.base_filter import FilterCore
from fastapi_sqlalchemy_filter.filters import FiltersList as fls

from db.models import MyModel


app = FastAPI()

my_item_filter = {
        'my_model_field_name(enum)': [fls.eq, fls.in_],
        'my_model_field_name(int)': [fls.between, fls.eq, fls.gt, fls.lt, fls.in_],
        'my_model_field_name(str)': [fls.like, fls.startswith, fls.contains, fls.eq, fls.in_],
        'my_model_field_name(datetime)': [fls.between, fls.in_, fls.eq, fls.gt, fls.lt]
    }

@app.get("/")
async def get_filtered_items(
             filter: str = Query(default=''),
             db: AsyncSession
            ):
    my_filter = FilterCore(MyModel, my_item_filter)
    query = my_filter.get_query(filter)
    res = await db.execute(query)
    return res.scalars().all()
```

### Example of work

```shell

 get_query(
      'salary_from__in_=60,70,80&'
      'created_at__between=2023-05-01,2023-05-05|'
      'category__eq=Medicine'
 )
   
 # Return SQLAlchemy orm query exact as:
           
    SELECT * from model
    WHERE model.salary_from  IN (60,70,80)
    AND model.created_at BETWEEN '2023-05-01' AND '2023-05-05'
    OR model.category = 'Medicine';
```

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