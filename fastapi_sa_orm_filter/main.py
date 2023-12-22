import json
from typing import Any, Dict, List, Type

import pydantic
from fastapi import HTTPException
from pydantic import create_model
from pydantic._internal._model_construction import ModelMetaclass
from sqlalchemy_to_pydantic import sqlalchemy_to_pydantic
from sqlalchemy import select
from sqlalchemy.orm import InstrumentedAttribute, DeclarativeMeta
from sqlalchemy.sql.elements import BinaryExpression, UnaryExpression
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
        self.model = model
        self._allowed_filters = allowed_filters
        self._model_serializer = self._create_pydantic_serializer()

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
        split_query = self.split_by_order_by(custom_filter)
        if len(split_query) == 1:
            complete_query = self.get_complete_query(split_query[0])
            return complete_query
        filter_query_str, order_by_query_str = split_query
        complete_query = self.get_complete_query(filter_query_str, order_by_query_str)
        return complete_query

    def get_complete_query(self, filter_query_str: str, order_by_query_str: str | None = None) -> Select[Any]:
        select_query_part = self.get_select_query_part()
        filter_query_part = self.get_filter_query_part(filter_query_str)
        complete_query = select_query_part.filter(*filter_query_part)
        group_query_part = self.get_group_by_query_part()
        if group_query_part != []:
            complete_query = complete_query.group_by(*group_query_part)
        if order_by_query_str is not None:
            order_by_query = self.get_order_by_query_part(order_by_query_str)
            complete_query = complete_query.order_by(*order_by_query)
        return complete_query

    def get_select_query_part(self) -> Select[Any]:
        return select(self.model)

    def get_filter_query_part(self, filter_query_str: str) -> List[Any]:
        conditions = self._get_filter_query(filter_query_str)
        if conditions == []:
            return conditions
        return [or_(*conditions)]

    def get_group_by_query_part(self):
        return []

    def get_order_by_query_part(self, order_by_query_str: str) -> List[UnaryExpression]:
        order_by_parser = _OrderByQueryParser(self.model)
        return order_by_parser.get_order_by_query(order_by_query_str)

    def _get_filter_query(self, custom_filter: str) -> List[BinaryExpression]:
        filter_conditions = []
        if custom_filter == '':
            return filter_conditions
        query_parser = _FilterQueryParser(custom_filter, self.model, self._allowed_filters)
        for and_expressions in query_parser.get_parsed_query():
            and_condition = []
            for expression in and_expressions:
                column, operator, value = expression
                serialized_dict = self._format_expression(column, operator, value)
                value = serialized_dict[column.name]
                param = self._get_orm_for_field(column, operator, value)
                and_condition.append(param)
            filter_conditions.append(and_(*and_condition))
        return filter_conditions

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
        pydantic_serializer = sqlalchemy_to_pydantic(self.model)
        optional_model = self._get_optional_pydantic_model(pydantic_serializer)
        optional_list_model = self._get_optional_pydantic_model(pydantic_serializer, is_list=True)
        return {"optional_model": optional_model, "optional_list_model": optional_list_model}

    def _get_orm_for_field(
        self, column: InstrumentedAttribute, operator: str, value: Any
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
                ).model_dump(exclude_none=True)
                return serialized_dict
            serialized_dict = self._model_serializer["optional_list_model"](
                **{column.name: value}
            ).model_dump(exclude_none=True)
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

    def _get_optional_pydantic_model(self, pydantic_serializer, is_list: bool = False):
        fields = {}
        for k, v in pydantic_serializer.model_fields.items():
            origin_annotation = getattr(v, 'annotation')
            if is_list:
                fields[k] = (List[origin_annotation], None)
            else:
                fields[k] = (origin_annotation, None)
        pydantic_model = create_model(self.model.__name__, **fields)
        return pydantic_model
