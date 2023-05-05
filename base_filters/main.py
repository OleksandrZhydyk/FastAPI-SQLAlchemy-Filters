import json
from datetime import datetime
from enum import Enum

from fastapi import HTTPException
from pydantic import create_model
from pydantic_sqlalchemy import sqlalchemy_to_pydantic
from sqlalchemy import select
from sqlalchemy.sql.expression import and_, or_, cast
from starlette import status
from sqlalchemy.types import Date, DateTime


class FiltersList(str, Enum):
    eq = "__eq__"
    gt = "__gt__"
    lt = "__lt__"
    gte = '__gte__'
    lte = '__lte__'
    in_ = "in_"
    startswith = "startswith"
    endswith = 'endswith'
    between = "between"
    like = "like"
    ilike = "ilike"
    contains = 'contains'
    icontains = 'icontains'
    not_eq = '__ne__'
    not_in = 'not_in'
    not_like = "not_like"
    not_between = 'not_between'


class FilterCore:
    def __init__(self, model, allowed_filters):
        self.model = model
        self.allowed_filters = allowed_filters
        self.model_serializator = self.create_pydantic_serializator()

    # async def get_query(self, filter, db):
    #     if not filter:
    #         query = select(self.model)
    #         return query
    #     params = self.parser_by_operator(filter)
    #     conditions = []
    #     for param in params:
    #         field_name, condition = param.split('__')
    #         column = getattr(self.model, field_name)
    #         operator, value = condition.split("=")
    #         self.validate_query_params(field_name, operator)
    #         value = self.format_value(value, operator, column)
    #         if operator == 'between':
    #             conditions.append(getattr(column, FiltersList[operator].value)(*value))
    #         else:
    #             conditions.append(getattr(column, FiltersList[operator].value)(value))
    #     query = select(self.model).filter(and_(*conditions))
    #     return query
    # @staticmethod
    # def parser_by_operator(filter):
    #     dct = {}
    #     param = ""
    #     for i in filter:
    #         if i in ['|', '&']:
    #             dct[param] = i
    #             param = ""
    #         else:
    #             param += i
    #     dct[param] = ""
    #     return dct

    def get_or_query(self, filter):
        if not filter:
            query = select(self.model)
            return query
        conditions = []
        and_blocks = self.parse_by_or(filter)
        for and_block in and_blocks:
            and_condition = []
            for expression in and_block:
                field_name, condition = expression.split('__')
                column = getattr(self.model, field_name)
                operator, value = condition.split("=")
                self.validate_query_params(field_name, operator)

                serialized_dict = self.model_serializator(**{field_name: value}).dict(exclude_none=True)
                value = serialized_dict[field_name]
                print(value)
                # value = self.format_value(value, operator, column)
                if isinstance(column.type, DateTime):
                    param = self.get_orm_for_date_field(column, operator, value)
                    and_condition.append(param)
                else:
                    param = self.get_orm_for_field(column, operator, value)
                    and_condition.append(param)
            conditions.append(and_(*and_condition))
        query = select(self.model).filter(or_(*conditions))
        return query

    def create_pydantic_serializator(self):
        pydantic_serializer = sqlalchemy_to_pydantic(self.model)
        optionalized = {f.name: (f.type_, None) for f in pydantic_serializer.__fields__.values()}
        return create_model(self.model.__name__, **optionalized)

    @staticmethod
    def parse_by_or(filter):
        and_blocks = [block.split("&") for block in filter.split("|")]
        # and_blocks = [['description__contains=test', 'salary_from__eq=10'], ['category__eq=finance']]
        return and_blocks

    @staticmethod
    def get_orm_for_date_field(column, operator, value):
        if operator in [FiltersList.between]:
            param = getattr(cast(column, Date), FiltersList[operator].value)(*value)
        else:
            param = getattr(cast(column, Date), FiltersList[operator].value)(value)
        return param

    @staticmethod
    def get_orm_for_field(column, operator, value):
        if operator in [FiltersList.between]:
            param = getattr(column, FiltersList[operator].value)(*value)
        else:
            param = getattr(column, FiltersList[operator].value)(value)
        return param


    def format_value(self, value, operator, column):
        if not isinstance(column.type, DateTime) and operator in ['between', 'in_']:
            try:

                value = json.loads(value.replace("'", '"'))
            except:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Incorrect filter values '{value}'"
                )
        if isinstance(column.type, DateTime):
            if operator in ['between', 'contains']:
                serialized_date = json.loads(value.replace("'", '"'))
                value = [datetime.strptime(date_str, '%Y-%m-%d').date() for date_str in serialized_date]
            else:
                value = datetime.strptime(value, '%Y-%m-%d').date()
        return value

    def validate_query_params(self, field_name, operator):
        if field_name not in self.allowed_filters:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden filter field '{field_name}'"
            )
        for allow_filter in self.allowed_filters[field_name]:
            if operator == allow_filter.name:
                return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Forbidden filter '{operator}' for '{field_name}'"
        )


# class AllowedFieldsAndFilters(BaseModel):
#     def __init__(self, model):
#         for column_name in model.__table__.columns.keys():
#             setattr(self, column_name, [])
