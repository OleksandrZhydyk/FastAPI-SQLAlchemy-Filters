"""FastAPI-SQLAlchemy filter, transform request query string to SQLAlchemy orm query"""
from fastapi_sa_orm_filter.main import FilterCore # noqa
from fastapi_sa_orm_filter.operators import Operators as ops # noqa

__version__ = "0.2.5"

from .main import FilterCore as FilterCore # noqa
from .operators import Operators as Operators # noqa
