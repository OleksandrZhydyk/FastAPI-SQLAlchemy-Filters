from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql.elements import UnaryExpression

from fastapi_sa_orm_filter.dto import ParsedFilter
from fastapi_sa_orm_filter.exceptions import SAFilterOrmException
from fastapi_sa_orm_filter.operators import Operators as ops
from fastapi_sa_orm_filter.operators import OrderSequence


class OrderByQueryParser:
    """
    Class parse order by part of request query string.
    """
    def __init__(self, model: type[DeclarativeBase]) -> None:
        self._model = model

    def get_order_by_query(self, order_by_query_str: str) -> list[UnaryExpression]:
        order_by_fields = self._validate_order_by_fields(order_by_query_str)
        order_by_query = []
        for field in order_by_fields:
            if '-' in field:
                column = getattr(self._model, field.strip('-'))
                order_by_query.append(getattr(column, OrderSequence.desc)())
            else:
                column = getattr(self._model, field.strip('+'))
                order_by_query.append(getattr(column, OrderSequence.asc)())
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


class FilterQueryParser:
    """
    Class parse filter part of request query string.
    """

    def __init__(
            self, query: str,
            allowed_filters: dict[str, list[ops]]
    ) -> None:
        self._query = query
        self._allowed_filters = allowed_filters

    def get_parsed_query(self) -> list[list[ParsedFilter]]:
        """
        :return:
            [
                [ParsedFilter, ParsedFilter, ParsedFilter]
            ]
        """
        and_blocks = self._parse_by_conjunctions()
        parsed_query = []
        for and_block in and_blocks:
            parsed_and_blocks = []
            for expression in and_block:
                parsed_filter = self._parse_expression(expression)
                self._validate_query_params(parsed_filter.field_name, parsed_filter.operator)
                parsed_and_blocks.append(parsed_filter)
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
    ) -> ParsedFilter:
        relation = None
        try:
            field_name, condition = expression.split("__")
            if "." in field_name:
                relation, field_name = self._get_relation_model(field_name)
            operator, value = condition.split("=")
        except ValueError:
            raise SAFilterOrmException(
                "Incorrect filter request syntax,"
                " please use pattern :"
                "'{field_name}__{condition}={value}{conjunction}' "
                "or '{relation}.{field_name}__{condition}={value}{conjunction}'",
            )

        return ParsedFilter(field_name=field_name, operator=operator, value=value, relation=relation)

    def _get_relation_model(self, field_name: str) -> list[str]:
        return field_name.split(".")

    def _validate_query_params(
        self, field_name: str, operator: str
    ) -> None:
        """
        Check expression on valid and allowed field_name and operator
        """
        if field_name not in self._allowed_filters:
            raise SAFilterOrmException(f"Forbidden filter field '{field_name}'")
        for allow_filter in self._allowed_filters[field_name]:
            if operator == allow_filter.name:
                return
        raise SAFilterOrmException(f"Forbidden filter '{operator}' for '{field_name}'")
