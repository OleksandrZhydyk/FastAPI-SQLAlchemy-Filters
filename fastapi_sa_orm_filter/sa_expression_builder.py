import json
from typing import Any

import pydantic
from pydantic import create_model
from pydantic._internal._model_construction import ModelMetaclass
from sqlalchemy import inspect, BinaryExpression, and_
from sqlalchemy.orm import DeclarativeBase, InstrumentedAttribute
from sqlalchemy_to_pydantic import sqlalchemy_to_pydantic

from fastapi_sa_orm_filter.exceptions import SAFilterOrmException
from fastapi_sa_orm_filter.operators import Operators as ops


class SAFilterExpressionBuilder:

    def __init__(self, model: type[DeclarativeBase]) -> None:
        self.model = model
        self._relationships = inspect(model).relationships.items()
        self._model_serializers = self.create_pydantic_serializers()

    def get_expressions(self, parsed_filters) -> list[BinaryExpression]:
        model = self.model
        table = self.model.__tablename__

        or_expr = []

        for and_parsed_filter in parsed_filters:
            and_expr = []
            for and_filter in and_parsed_filter:
                if and_filter.has_relation:
                    model = self.get_relation_model(and_filter.relation)
                    table = model.__tablename__
                column = self.get_column(model, and_filter.field_name)
                serialized_dict = self.serialize_expression_value(table, column, and_filter.operator, and_filter.value)
                value = serialized_dict[column.name]
                expr = self.get_orm_for_field(column, and_filter.operator, value)
                and_expr.append(expr)
            or_expr.append(and_(*and_expr))
        return or_expr

    def get_relation_model(self, relation: str) -> DeclarativeBase:
        for relationship in self._relationships:
            if relationship[0] == relation:
                return relationship[1].mapper.class_
        raise SAFilterOrmException(f"Can not find relation {relation} in {self.model.__name__} model")

    def get_column(self, model: type[DeclarativeBase], field_name: str) -> InstrumentedAttribute:
        column = getattr(model, field_name, None)

        if not column:
            raise SAFilterOrmException(f"DB model {model.__name__} doesn't have field '{field_name}'")
        return column

    def create_pydantic_serializers(self) -> dict[str, dict[str, ModelMetaclass]]:
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
        models.extend(self.get_relations_classes())

        serializers = {}

        for model in models:
            pydantic_serializer = sqlalchemy_to_pydantic(model)
            optional_model = self.get_optional_pydantic_model(model, pydantic_serializer)
            optional_list_model = self.get_optional_pydantic_model(model, pydantic_serializer, is_list=True)

            serializers[model.__tablename__] = {
                "optional_model": optional_model, "optional_list_model": optional_list_model
            }

        return serializers

    def get_relations_classes(self) -> list:
        return [relation[1].mapper.class_ for relation in self._relationships]

    def get_orm_for_field(
            self, column: InstrumentedAttribute, operator: str, value: Any
    ) -> BinaryExpression:
        """
        Create SQLAlchemy orm expression for the field
        """
        if operator in [ops.between]:
            return getattr(column, ops[operator].value)(*value)
        return getattr(column, ops[operator].value)(value)

    def serialize_expression_value(
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
    def get_optional_pydantic_model(model, pydantic_serializer, is_list: bool = False):
        fields = {}
        for k, v in pydantic_serializer.model_fields.items():
            origin_annotation = getattr(v, 'annotation')
            if is_list:
                fields[k] = (list[origin_annotation], None)
            else:
                fields[k] = (origin_annotation, None)
        pydantic_model = create_model(model.__name__, **fields)
        return pydantic_model
