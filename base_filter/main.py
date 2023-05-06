import json
from datetime import datetime
from typing import Any, Dict, List, Tuple

import pydantic
from fastapi import HTTPException
from pydantic import create_model
from pydantic.main import ModelMetaclass
from pydantic_sqlalchemy import sqlalchemy_to_pydantic
from sqlalchemy import select
from sqlalchemy.orm import InstrumentedAttribute, DeclarativeMeta
from sqlalchemy.sql.elements import BinaryExpression
from sqlalchemy.sql.expression import and_, or_
from starlette import status
from sqlalchemy.types import Date, DateTime
from sqlalchemy.sql import Select

from base_filter.filters import FiltersList as fls


class FilterCore:
    """
        Class serves of SQLAlchemy orm query creation and provides simple API

        :param model: declared SQLAlchemy db model
        :param allowed_filters: dict with

        :return: Average temperature
    """

    def __init__(self, model: DeclarativeMeta, allowed_filters: Dict[str, List[fls]]) -> None:
        self.model = model
        self.allowed_filters = allowed_filters

    def get_query(self, custom_filter: str) -> Select:
        """
            Construct the SQLAlchemy orm query from request query string

            >>> get_query(
            >>>    'salary_from__in_=60,70,80&'
            >>>    'created_at__between=2023-05-01,2023-05-05|'
            >>>    'category__eq=Medicine'
            >>>    )

            SELECT * from model
            WHERE model.salary_from  IN (60,70,80)
            AND model.created_at BETWEEN '2023-05-01' AND '2023-05-05'
            OR model.category = 'Medicine';

            :param custom_filter: request query string with fields and filter conditions
            :return: SQLAlchemy orm query
        """
        # checking on empty filter query, return all objects
        if not custom_filter:
            query = select(self.model)
            return query
        conditions = []
        and_blocks = self._parse_by_or(custom_filter)
        for and_block in and_blocks:
            and_condition = []
            for expression in and_block:
                column, operator, value = self._expression_parser(expression)
                self._validate_query_params(column.name, operator)
                serialized_dict = self._format_value(value, operator, column)
                value = serialized_dict[column.name]
                param = self._get_orm_for_field(column, operator, value)
                and_condition.append(param)
            conditions.append(and_(*and_condition))
        query = select(self.model).filter(or_(*conditions))
        return query

    def _expression_parser(self, expression: str) -> Tuple[InstrumentedAttribute, str, str]:
        try:
            field_name, condition = expression.split('__')
            operator, value = condition.split("=")
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect filter request syntax,"
                       " please use pattern :"
                       "'{field_name}__{condition}={value}{conjunction}'"
            )
        if not hasattr(self.model, field_name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"DB model {self.model} doesn't have field '{field_name}'"
            )
        else:
            column = getattr(self.model, field_name)
        return column, operator, value

    def _create_pydantic_serializer(self) -> Dict[str, ModelMetaclass]:
        pydantic_serializer = sqlalchemy_to_pydantic(self.model)
        fields_to_optional = {f.name: (f.type_, None) for f in pydantic_serializer.__fields__.values()}
        fields_wrap_to_list = {f.name: (List[f.type_], None) for f in pydantic_serializer.__fields__.values()}
        optional_model = create_model(self.model.__name__, **fields_to_optional)
        list_model = create_model(self.model.__name__, **fields_wrap_to_list)
        return {'optional_model': optional_model, 'list_model': list_model}

    @staticmethod
    def _parse_by_or(custom_filter: str) -> List[List[str]]:
        and_blocks = [block.split("&") for block in custom_filter.split("|")]
        # and_blocks = [['description__contains=test', 'salary_from__eq=10'], ['category__eq=finance']]
        return and_blocks

    @staticmethod
    def _get_orm_for_field(column: InstrumentedAttribute, operator: str, value: Any) -> BinaryExpression:
        if operator in [fls.between]:
            param = getattr(column, fls[operator].value)(*value)
        else:
            param = getattr(column, fls[operator].value)(value)
        return param

    def _format_value(self, value: str, operator: str, column) -> dict[str, Any]:
        model_serializer = self._create_pydantic_serializer()
        value = value.split(',')
        try:
            if isinstance(column.type, DateTime):
                value = [datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S') for date_str in value]
            elif isinstance(column.type, Date):
                value = [datetime.strptime(date_str, '%Y-%m-%d').date() for date_str in value]
            else:
                if operator not in [fls.between, fls.in_]:
                    value = value[0]
                    serialized_dict = model_serializer['optional_model'](**{column.name: value}).dict(exclude_none=True)
                    return serialized_dict
            serialized_dict = model_serializer['list_model'](**{column.name: value}).dict(exclude_none=True)
            return serialized_dict
        except pydantic.ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=json.loads(e.json())
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Incorrect filter value '{value}'"
            )

    def _validate_query_params(self, field_name: str, operator: str) -> None:
        if field_name not in self.allowed_filters:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Forbidden filter field '{field_name}'"
            )
        for allow_filter in self.allowed_filters[field_name]:
            if operator == allow_filter.name:
                return
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Forbidden filter '{operator}' for '{field_name}'"
        )