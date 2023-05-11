from typing import Optional, Tuple, Union, List, Any, Type, Dict

from fastapi import HTTPException
from sqlalchemy.orm import InstrumentedAttribute, DeclarativeMeta
from sqlalchemy.sql.elements import UnaryExpression
from starlette import status

from fastapi_sa_orm_filter.operators import Operators as ops
from fastapi_sa_orm_filter.operators import Sequence


class _OrderByQueryParser:
    """
    Class parse order by part of request query string.
    """
    def __init__(self, model: Type[DeclarativeMeta]) -> None:
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

    def _validate_order_by_fields(self, order_by_query_str: str) -> List[str]:
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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Incorrect order_by field name {field} for model {self._model}",
            )
        return order_by_fields


class _FilterQueryParser:
    """
    Class parse filter part of request query string.
    """

    def __init__(self, query: str, model: Type[DeclarativeMeta], allowed_filters: Dict[str, List[ops]]) -> None:
        self.query = query
        self.model = model
        self.allowed_filters = allowed_filters

    def get_parsed_query(self) -> List[List[Any]]:
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
                column, operator, value = self._parse_expression(expression)
                self._validate_query_params(column.name, operator)
                parsed_and_blocks.append([column, operator, value])
            parsed_query.append(parsed_and_blocks)
        return parsed_query

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
