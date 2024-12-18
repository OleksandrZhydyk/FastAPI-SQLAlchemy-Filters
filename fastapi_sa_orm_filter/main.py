from typing import Any, Type

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql.elements import BinaryExpression, UnaryExpression
from sqlalchemy.sql.expression import or_
from starlette import status
from sqlalchemy.sql import Select

from fastapi_sa_orm_filter.exceptions import SAFilterOrmException
from fastapi_sa_orm_filter.operators import Operators as ops
from fastapi_sa_orm_filter.parsers import FilterQueryParser, OrderByQueryParser
from fastapi_sa_orm_filter.sa_expression_builder import SAFilterExpressionBuilder


class FilterCore:
    """
    Class serves of SQLAlchemy orm query creation.
    Convert parsed query data to python data types and form SQLAlchemy query.
    """

    def __init__(
        self,
        model: Type[DeclarativeBase],
        allowed_filters: dict[str, list[ops]],
        select_query_part: Select[Any] | None = None
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
        self._allowed_filters = allowed_filters
        self.select_query_part = select_query_part

    def get_query(self, custom_filter: str) -> Select[Any]:
        """
        Construct the SQLAlchemy orm query from request query string

        :param custom_filter: request query string with fields and filter conditions
            salary_from__in_=60,70,80&
            created_at__between=2023-05-01,2023-05-05|
            category__eq=Medicine&
            order_by=-id
        :param select_query_part: custom select query part (select(model).join(model1))

        :return:
            select(model)
                .where(
                    or_(
                        and_(
                            model.salary_from.in_(60,70,80),
                            model.created_at.between(2023-05-01, 2023-05-05)
                        ),
                        model.category == 'Medicine'
                    ).order_by(model.id.desc())
        """
        split_query = self._split_by_order_by(custom_filter)
        try:
            complete_query = self._get_complete_query(*split_query)
        except SAFilterOrmException as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.args[0])
        return complete_query

    def _get_complete_query(self, filter_query_str: str, order_by_query_str: str | None = None) -> Select[Any]:
        select_query_part = self.get_select_query_part()
        filter_query_part = self._get_filter_query_part(filter_query_str)
        complete_query = select_query_part.filter(*filter_query_part)
        group_query_part = self.get_group_by_query_part()
        if group_query_part:
            complete_query = complete_query.group_by(*group_query_part)
        if order_by_query_str is not None:
            order_by_query = self.get_order_by_query_part(order_by_query_str)
            complete_query = complete_query.order_by(*order_by_query)
        return complete_query

    def get_select_query_part(self) -> Select[Any]:
        if self.select_query_part is not None:
            return self.select_query_part
        return select(self.model)

    def _get_filter_query_part(self, filter_query_str: str) -> list[Any]:
        conditions = self._get_filter_query(filter_query_str)
        if len(conditions) == 0:
            return conditions
        return [or_(*conditions)]

    def get_group_by_query_part(self) -> list:
        return []

    def get_order_by_query_part(self, order_by_query_str: str) -> list[UnaryExpression]:
        order_by_parser = OrderByQueryParser(self.model)
        return order_by_parser.get_order_by_query(order_by_query_str)

    def _get_filter_query(self, custom_filter: str) -> list[BinaryExpression]:
        filter_conditions = []
        if custom_filter == "":
            return filter_conditions

        parser = FilterQueryParser(custom_filter, self._allowed_filters)
        parsed_filters = parser.get_parsed_query()
        sa_builder = SAFilterExpressionBuilder(self.model)
        return sa_builder.get_expressions(parsed_filters)

    @staticmethod
    def _split_by_order_by(query) -> list:
        split_query = [query_part.strip("&") for query_part in query.split("order_by=")]
        if len(split_query) > 2:
            raise SAFilterOrmException("Use only one order_by directive")
        return split_query
