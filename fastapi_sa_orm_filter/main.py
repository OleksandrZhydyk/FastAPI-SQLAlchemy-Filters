import json
from typing import Any, Dict, List, Type

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
from sqlalchemy.sql import Select

from fastapi_sa_orm_filter.operators import Operators as ops
from fastapi_sa_orm_filter.parsers import _FilterQueryParser, _OrderByQueryParser


class FilterCore:
    """
    Class serves of SQLAlchemy orm query creation.
    Convert parsed query data to python data types and form SQLAlchemy query.
    """

    def __init__(
        self, model: Type[DeclarativeMeta], allowed_filters: Dict[str, List[ops]]
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
        self._model = model
        self._allowed_filters = allowed_filters
        self._model_serializer = self._create_pydantic_serializer()

    def get_query(self, custom_filter: str) -> Select:
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
        split_query = self.split_by_order_by(custom_filter)
        if len(split_query) == 1:
            filter_query = self._get_filter_query(split_query[0])
            return filter_query
        filter_query_str, order_by_query_str = split_query
        filter_query = self._get_filter_query(filter_query_str)
        order_by_query = _OrderByQueryParser(self._model).get_order_by_query(order_by_query_str)
        query = filter_query.order_by(*order_by_query)
        return query

    def _get_filter_query(self, custom_filter):
        if not custom_filter:
            query = select(self._model)
            return query
        conditions = []
        query_parser = _FilterQueryParser(custom_filter, self._model, self._allowed_filters)
        for and_expressions in query_parser.get_parsed_query():
            and_condition = []
            for expression in and_expressions:
                column, operator, value = expression
                serialized_dict = self._format_expression(column, operator, value)
                value = serialized_dict[column.name]
                param = self._get_orm_for_field(column, operator, value)
                and_condition.append(param)
            conditions.append(and_(*and_condition))
        query = select(self._model).filter(or_(*conditions))
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
                    field: Optional[List[type]]
        }
        """
        pydantic_serializer = sqlalchemy_to_pydantic(self._model)
        fields_to_optional = {
            f.name: (f.type_, None) for f in pydantic_serializer.__fields__.values()
        }
        fields_wrap_to_optional_list = {
            f.name: (List[f.type_], None)
            for f in pydantic_serializer.__fields__.values()
        }
        optional_model = create_model(self._model.__name__, **fields_to_optional)
        optional_list_model = create_model(self._model.__name__, **fields_wrap_to_optional_list)
        return {"optional_model": optional_model, "list_model": optional_list_model}

    @staticmethod
    def _get_orm_for_field(
        column: InstrumentedAttribute, operator: str, value: Any
    ) -> BinaryExpression:
        """
        Create SQLAlchemy orm expression for the field
        """
        if operator in [ops.between]:
            param = getattr(column, ops[operator].value)(*value)
        else:
            param = getattr(column, ops[operator].value)(value)
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
            if operator not in [ops.between, ops.in_]:
                value = value[0]
                serialized_dict = self._model_serializer["optional_model"](
                    **{column.name: value}
                ).dict(exclude_none=True)
                return serialized_dict
            serialized_dict = self._model_serializer["list_model"](
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

    @staticmethod
    def split_by_order_by(query):
        split_query = [query_part.strip("&") for query_part in query.split("order_by=")]
        if len(split_query) > 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Use only one order_by directive",
            )
        return split_query
