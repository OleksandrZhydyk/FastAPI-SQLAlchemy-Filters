import json
from datetime import datetime
from typing import Any, Dict, List, Tuple, Optional, Union

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

from fastapi_sa_orm_filter.filters import FiltersList as fls


class FilterCore:
    """
    Class serves of SQLAlchemy orm query creation.
    Convert parsed query data to python data types and form SQLAlchemy query.
    """

    def __init__(
        self, model: DeclarativeMeta, allowed_filters: Dict[str, List[fls]]
    ) -> None:
        """
        Produce a class:`FilterCore` object against a function

        :param model: declared SQLAlchemy db model
        :param allowed_filters: dict with allowed model fields and operators
            for filter, like:
                {
                    'field_name': [startswith, eq, in_],
                    'field_name': [contains, like]
                }
        """
        self.model = model
        self.allowed_filters = allowed_filters
        self.model_serializer = self._create_pydantic_serializer()

    def get_query(self, custom_filter: str) -> Select:
        """
        Construct the SQLAlchemy orm query from request query string

        >>> get_query(
        >>>    'salary_from__in_=60,70,80&'
        >>>    'created_at__between=2023-05-01,2023-05-05|'
        >>>    'category__eq=Medicine'
        >>>    )


        :param custom_filter: request query string with fields and filter conditions
            'salary_from__in_=60,70,80&
             created_at__between=2023-05-01,2023-05-05|
             category__eq=Medicine'
        :return:
            select(model)
                .where(
                    or_(
                        and_(
                            model.salary_from.in_(60,70,80),
                            model.created_at.between(2023-05-01, 2023-05-05)
                            ),
                        model.category == 'Medicine'
                    )
        """
        if not custom_filter:
            query = select(self.model)
            return query
        conditions = []
        query_parser = QueryParser(custom_filter, self.model, self.allowed_filters)
        for and_expressions in query_parser.get_parsed_query():
            and_condition = []
            for expression in and_expressions:
                column, operator, value = expression
                serialized_dict = self._format_expression(column, operator, value)
                value = serialized_dict[column.name]
                param = self._get_orm_for_field(column, operator, value)
                and_condition.append(param)
            conditions.append(and_(*and_condition))
        query = select(self.model).filter(or_(*conditions))
        return query

    def _create_pydantic_serializer(self) -> Dict[str, ModelMetaclass]:
        """
        Create two pydantic models (optional and list field types)
        for value: str serialization

        :return: {
            'optional_model':
                class model.__name__(BaseModel):
                    field: Optional[type]
            'list_model':
                class model.__name__(BaseModel):
                    field: List[type]
        }
        """
        pydantic_serializer = sqlalchemy_to_pydantic(self.model)
        fields_to_optional = {
            f.name: (f.type_, None) for f in pydantic_serializer.__fields__.values()
        }
        fields_wrap_to_list = {
            f.name: (List[f.type_], None)
            for f in pydantic_serializer.__fields__.values()
        }
        optional_model = create_model(self.model.__name__, **fields_to_optional)
        list_model = create_model(self.model.__name__, **fields_wrap_to_list)
        return {"optional_model": optional_model, "list_model": list_model}

    @staticmethod
    def _get_orm_for_field(
        column: InstrumentedAttribute, operator: str, value: Any
    ) -> BinaryExpression:
        """
        Create SQLAlchemy orm expression for the field
        """
        if operator in [fls.between]:
            param = getattr(column, fls[operator].value)(*value)
        else:
            param = getattr(column, fls[operator].value)(value)

        return param

    def _format_expression(
        self, column: InstrumentedAttribute, operator: str, value: str
    ) -> dict[str, Any]:
        """
        Serialize expression value from string to python type value,
        according to db model types

        :return: {'field_name': [value, value]}
        """
        value = value.split(",")
        try:
            if isinstance(column.type, DateTime):
                value = [
                    datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                    for date_str in value
                ]
            elif isinstance(column.type, Date):
                value = [
                    datetime.strptime(date_str, "%Y-%m-%d").date() for date_str in value
                ]
            else:
                if operator not in [fls.between, fls.in_]:
                    value = value[0]
                    serialized_dict = self.model_serializer["optional_model"](
                        **{column.name: value}
                    ).dict(exclude_none=True)
                    return serialized_dict
            serialized_dict = self.model_serializer["list_model"](
                **{column.name: value}
            ).dict(exclude_none=True)
            return serialized_dict
        except pydantic.ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=json.loads(e.json())
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Incorrect filter value '{value}'",
            )


class QueryParser:
    """
    Class parse request query string.
    """

    def __init__(self, query, model, allowed_filters):
        self.query = query
        self.model = model
        self.allowed_filters = allowed_filters

    def get_parsed_query(self):
        """
        :return:
            [
                [[column, operator, value], [column, operator, value]],
                [[column, operator, value]]
            ]
        """
        and_blocks = self._parse_by_conjunctions()
        par = []
        for and_block in and_blocks:
            parsed_and_blocks = []
            for expression in and_block:
                column, operator, value = self._parse_expression(expression)
                self._validate_query_params(column.name, operator)
                parsed_and_blocks.append([column, operator, value])
            par.append(parsed_and_blocks)
        return par

    def _parse_by_conjunctions(self) -> List[List[str]]:
        """
        Split request query string by 'OR' and 'AND' conjunctions
        to divide query string to field's conditions

        :return: [
                    ['field_name__operator=value', 'field_name__operator=value'],
                    ['field_name__operator=value']
                ]
        """
        and_blocks = [block.split("&") for block in self.query.split("|")]
        return and_blocks

    def _parse_expression(
        self, expression: str
    ) -> Union[Tuple[InstrumentedAttribute, str, str], HTTPException]:
        try:
            field_name, condition = expression.split("__")
            operator, value = condition.split("=")
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect filter request syntax,"
                " please use pattern :"
                "'{field_name}__{condition}={value}{conjunction}'",
            )
        if not hasattr(self.model, field_name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"DB model {self.model} doesn't have field '{field_name}'",
            )
        else:
            column = getattr(self.model, field_name)
        return column, operator, value

    def _validate_query_params(
        self, field_name: str, operator: str
    ) -> Optional[HTTPException]:
        """
        Check expression on valid and allowed field_name and operator
        """
        if field_name not in self.allowed_filters:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Forbidden filter field '{field_name}'",
            )
        for allow_filter in self.allowed_filters[field_name]:
            if operator == allow_filter.name:
                return
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Forbidden filter '{operator}' for '{field_name}'",
        )
