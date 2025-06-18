from fastapi_sa_orm_filter.dto import ParsedFilter
from fastapi_sa_orm_filter.exceptions import SAFilterOrmException
from fastapi_sa_orm_filter.interfaces import QueryParser
from fastapi_sa_orm_filter.operators import Operators as ops


class StringQueryParser(QueryParser):

    def __init__(self, custom_filter: str, allowed_filters: dict[str, list[ops]]) -> None:
        self.custom_filter = custom_filter
        self.allowed_filters = allowed_filters

    def get_parsed_filter(self) -> tuple[list[list[ParsedFilter]], list[str]] | tuple[list, list]:
        parsed_filter = []
        parsed_order_by = []

        if self.custom_filter == "":
            return parsed_filter, parsed_order_by

        split_query = [query_part.strip("&") for query_part in self.custom_filter.split("order_by=")]

        if len(split_query) > 2:
            raise SAFilterOrmException("Use only one order_by directive")

        parsed_filter = self._get_filter_query_part(split_query[0])

        if len(split_query) == 2:
            parsed_order_by = self._get_order_by_query_part(split_query[1])

        return parsed_filter, parsed_order_by

    def _get_filter_query_part(self, filter_query_str: str) -> list[list[ParsedFilter]] | list:
        if filter_query_str == "":
            return []
        filter_parser = StringFilterQueryParser(self.allowed_filters)
        return filter_parser.get_parsed_query(filter_query_str)

    def _get_order_by_query_part(self, order_by_query_str: str) -> list[str] | list:
        if order_by_query_str == "":
            return []
        order_by_parser = StringOrderByQueryParser()
        return order_by_parser.get_order_by_query(order_by_query_str)


class StringOrderByQueryParser:
    """
    Class parse order by part of request query string.
    """
    def get_order_by_query(self, order_by_query_str: str) -> list[str]:
        return order_by_query_str.split(",")


class StringFilterQueryParser:
    """
    Class parse filter part of request query string.
    """

    def __init__(
            self, allowed_filters: dict[str, list[ops]]
    ) -> None:
        self._allowed_filters = allowed_filters

    def get_parsed_query(self, filter_query_str: str) -> list[list[ParsedFilter]]:
        """
        :return:
            [
                [ParsedFilter, ParsedFilter, ParsedFilter]
            ]
        """
        and_blocks = self._parse_by_conjunctions(filter_query_str)
        parsed_query = []
        for and_block in and_blocks:
            parsed_and_blocks = []
            for expression in and_block:
                parsed_filter = self._parse_expression(expression)
                self._validate_query_params(parsed_filter.field_name, parsed_filter.operator)
                parsed_and_blocks.append(parsed_filter)
            parsed_query.append(parsed_and_blocks)
        return parsed_query

    def _parse_by_conjunctions(self, filter_query_str: str) -> list[list[str]]:
        """
        Split request query string by 'OR' and 'AND' conjunctions
        to divide query string to field's conditions

        :return: [
                    ['field_name__operator=value', 'field_name__operator=value'],
                    ['field_name__operator=value']
                ]
        """
        and_blocks = [block.split("&") for block in filter_query_str.split("|")]
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
