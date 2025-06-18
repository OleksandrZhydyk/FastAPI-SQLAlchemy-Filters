from typing import Any, Type

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql.elements import BinaryExpression, UnaryExpression
from sqlalchemy.sql.expression import or_
from starlette import status
from sqlalchemy.sql import Select

from fastapi_sa_orm_filter.dto import ParsedFilter
from fastapi_sa_orm_filter.exceptions import SAFilterOrmException
from fastapi_sa_orm_filter.interfaces import QueryParser
from fastapi_sa_orm_filter.operators import Operators as ops
from fastapi_sa_orm_filter.parsers import StringQueryParser
from fastapi_sa_orm_filter.sa_expression_builder import SAFilterExpressionBuilder, SAOrderByExpressionBuilder


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
        :param select_query_part: custom select query part (select(model).join(model1))
        """
        self.model = model
        self._allowed_filters = allowed_filters
        self.select_sql_query = select_query_part

    def get_query(self, custom_filter: str) -> Select[Any]:
        """
        Construct the SQLAlchemy orm query from request query string

        :param custom_filter: request query string with fields and filter conditions
            salary_from__in_=60,70,80&
            created_at__between=2023-05-01,2023-05-05|
            category__eq=Medicine&
            order_by=-id

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
        try:
            query_parser = self._get_query_parser(custom_filter)
            filter_query, order_by_query = query_parser.get_parsed_filter()
            complete_query = self._get_complete_query(filter_query, order_by_query)
        except SAFilterOrmException as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.args[0])
        return complete_query

    def _get_complete_query(
            self, filter_query: list[list[ParsedFilter]] | list, order_by_query: list[str] | list
    ) -> Select[Any]:
        select_sa_query = self.get_select_query_part()
        filter_sa_query = self._get_filter_sa_query(filter_query)
        group_by_sa_query = self._get_group_by_sa_query()
        order_by_sa_query = self._get_order_by_sa_query(order_by_query)
        return select_sa_query.filter(*filter_sa_query).group_by(*group_by_sa_query).order_by(*order_by_sa_query)

    def get_select_query_part(self) -> Select[Any]:
        if self.select_sql_query is not None:
            return self.select_sql_query
        return select(self.model)

    def _get_filter_sa_query(self, filter_query: list[list[ParsedFilter]] | list) -> list[BinaryExpression] | list:
        if len(filter_query) == 0:
            return []
        sa_builder = SAFilterExpressionBuilder(self.model)
        conditions = sa_builder.get_expressions(filter_query)
        return [or_(*conditions)]

    def _get_order_by_sa_query(self, order_by_query: list[str] | list) -> list[UnaryExpression]:
        if len(order_by_query) == 0:
            return []
        sa_builder = SAOrderByExpressionBuilder(self.model)
        return sa_builder.get_order_by_query(order_by_query)

    def _get_group_by_sa_query(self) -> list[BinaryExpression] | list:
        group_query_part = self.get_group_by_query_part()
        if len(group_query_part) == 0:
            return []
        return group_query_part

    def get_group_by_query_part(self) -> list:
        return []

    def _get_query_parser(self, custom_filter: str) -> QueryParser:
        return StringQueryParser(custom_filter, self._allowed_filters)
