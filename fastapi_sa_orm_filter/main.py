import json

from typing import Any, Type

import pydantic
from fastapi import HTTPException
from pydantic import create_model
from pydantic._internal._model_construction import ModelMetaclass
from sqlalchemy_to_pydantic import sqlalchemy_to_pydantic
from sqlalchemy import select, inspect
from sqlalchemy.orm import InstrumentedAttribute, DeclarativeBase
from sqlalchemy.sql.elements import BinaryExpression, UnaryExpression
from sqlalchemy.sql.expression import and_, or_
from starlette import status
from sqlalchemy.sql import Select

from fastapi_sa_orm_filter.exceptions import SAFilterOrmException
from fastapi_sa_orm_filter.operators import Operators as ops
from fastapi_sa_orm_filter.parsers import _FilterQueryParser, _OrderByQueryParser


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
        self.relationships = inspect(self.model).relationships.items()
        self._allowed_filters = allowed_filters
        self._model_serializers = self._create_pydantic_serializers()
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
        order_by_parser = _OrderByQueryParser(self.model)
        return order_by_parser.get_order_by_query(order_by_query_str)

    def _get_filter_query(self, custom_filter: str) -> list[BinaryExpression]:
        filter_conditions = []
        if custom_filter == "":
            return filter_conditions
        query_parser = _FilterQueryParser(custom_filter, self.model, self._allowed_filters)

        for and_expressions in query_parser.get_parsed_query():
            and_condition = []
            for expression in and_expressions:
                table, column, operator, value = expression
                serialized_dict = self._format_expression(table, column, operator, value)
                value = serialized_dict[column.name]
                param = self._get_orm_for_field(column, operator, value)
                and_condition.append(param)
            filter_conditions.append(and_(*and_condition))
        return filter_conditions

    def _create_pydantic_serializers(self) -> dict[str, dict[str, ModelMetaclass]]:
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

        models = [self.model]
        models.extend(self._get_relations())

        serializers = {}

        for model in models:
            pydantic_serializer = sqlalchemy_to_pydantic(model)
            optional_model = self._get_optional_pydantic_model(model, pydantic_serializer)
            optional_list_model = self._get_optional_pydantic_model(model, pydantic_serializer, is_list=True)

            serializers[model.__tablename__] = {
                "optional_model": optional_model, "optional_list_model": optional_list_model
            }

        return serializers

    def _get_relations(self) -> list:
        return [relation[1].mapper.class_ for relation in self.relationships]

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
        self, table: str, column: InstrumentedAttribute, operator: str, value: str
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
                model_serializer = self._model_serializers[table]["optional_model"]
            else:
                model_serializer = self._model_serializers[table]["optional_list_model"]
            return model_serializer(**{column.name: value}).model_dump(exclude_none=True)
        except pydantic.ValidationError as e:
            raise SAFilterOrmException(json.loads(e.json()))
        except ValueError:
            raise SAFilterOrmException(f"Incorrect filter value '{value}'")

    @staticmethod
    def _split_by_order_by(query) -> list:
        split_query = [query_part.strip("&") for query_part in query.split("order_by=")]
        if len(split_query) > 2:
            raise SAFilterOrmException("Use only one order_by directive")
        return split_query

    def _get_optional_pydantic_model(self, model, pydantic_serializer, is_list: bool = False):
        fields = {}
        for k, v in pydantic_serializer.model_fields.items():
            origin_annotation = getattr(v, 'annotation')
            if is_list:
                fields[k] = (list[origin_annotation], None)
            else:
                fields[k] = (origin_annotation, None)
        pydantic_model = create_model(model.__name__, **fields)
        return pydantic_model
