from typing import Optional, Tuple, Union, List, Any, Type

from fastapi import HTTPException
from sqlalchemy import inspect
from sqlalchemy.orm import InstrumentedAttribute, DeclarativeBase
from sqlalchemy.sql.elements import UnaryExpression

from fastapi_sa_orm_filter.exceptions import SAFilterOrmException
from fastapi_sa_orm_filter.operators import Operators as ops
from fastapi_sa_orm_filter.operators import Sequence


class _OrderByQueryParser:
    """
    Class parse order by part of request query string.
    """
    def __init__(self, model: Type[DeclarativeBase]) -> None:
        self._model = model

    def get_order_by_query(self, order_by_query_str: str) -> List[UnaryExpression]:
        order_by_fields = self._validate_order_by_fields(order_by_query_str)
        order_by_query = []
        for field in order_by_fields:
            if '-' in field:
                column = getattr(self._model, field.strip('-'))
                order_by_query.append(getattr(column, Sequence.desc)())
            else:
                column = getattr(self._model, field.strip('+'))
                order_by_query.append(getattr(column, Sequence.asc)())
        return order_by_query

    def _validate_order_by_fields(self, order_by_query_str: str) -> list[str]:
        """
        :return:
            [
                +field_name,
                -field_name
            ]
        """
        order_by_fields = order_by_query_str.split(",")
        model_fields = self._model.__table__.columns.keys()
        for field in order_by_fields:
            field = field.strip('+').strip('-')
            if field in model_fields:
                continue
            raise SAFilterOrmException(f"Incorrect order_by field name {field} for model {self._model.__name__}")
        return order_by_fields


class _FilterQueryParser:
    """
    Class parse filter part of request query string.
    """

    def __init__(self, query: str, model: Type[DeclarativeBase], allowed_filters: dict[str, list[ops]]) -> None:
        self._query = query
        self._model = model
        self._relationships = inspect(model).relationships.items()
        self._allowed_filters = allowed_filters

    def get_parsed_query(self) -> list[list[Any]]:
        """
        :return:
            [
                [[column, operator, value], [column, operator, value]],
                [[column, operator, value]]
            ]
        """
        and_blocks = self._parse_by_conjunctions()
        parsed_query = []
        for and_block in and_blocks:
            parsed_and_blocks = []
            for expression in and_block:
                table, column, operator, value = self._parse_expression(expression)
                self._validate_query_params(column.name, operator)
                parsed_and_blocks.append([table, column, operator, value])
            parsed_query.append(parsed_and_blocks)
        return parsed_query

    def _parse_by_conjunctions(self) -> list[list[str]]:
        """
        Split request query string by 'OR' and 'AND' conjunctions
        to divide query string to field's conditions

        :return: [
                    ['field_name__operator=value', 'field_name__operator=value'],
                    ['field_name__operator=value']
                ]
        """
        and_blocks = [block.split("&") for block in self._query.split("|")]
        return and_blocks

    def _parse_expression(
        self, expression: str
    ) -> Union[Tuple[str, InstrumentedAttribute, str, str], HTTPException]:
        model = self._model
        table = self._model.__tablename__
        try:
            field_name, condition = expression.split("__")
            if "." in field_name:
                model, table, field_name = self._get_relation_model(field_name)
            operator, value = condition.split("=")
        except ValueError:
            raise SAFilterOrmException(
                "Incorrect filter request syntax,"
                " please use pattern :"
                "'{field_name}__{condition}={value}{conjunction}' "
                "or '{relation}.{field_name}__{condition}={value}{conjunction}'",
            )

        column = getattr(model, field_name, None)

        if not column:
            raise SAFilterOrmException(f"DB model {model.__name__} doesn't have field '{field_name}'")
        return table, column, operator, value

    def _get_relation_model(self, field_name: str) -> tuple[DeclarativeBase, str, str]:
        relation, field_name = field_name.split(".")
        for relationship in self._relationships:
            if relationship[0] == relation:
                model = relationship[1].mapper.class_
                return model, model.__tablename__, field_name
        raise SAFilterOrmException(f"Can not find relation {relation} in {self._model.__name__} model")

    def _validate_query_params(
        self, field_name: str, operator: str
    ) -> Optional[HTTPException]:
        """
        Check expression on valid and allowed field_name and operator
        """
        if field_name not in self._allowed_filters:
            raise SAFilterOrmException(f"Forbidden filter field '{field_name}'")
        for allow_filter in self._allowed_filters[field_name]:
            if operator == allow_filter.name:
                return
        raise SAFilterOrmException(f"Forbidden filter '{operator}' for '{field_name}'")
