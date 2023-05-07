from enum import Enum


class FiltersList(str, Enum):
    eq = "__eq__"
    gt = "__gt__"
    lt = "__lt__"
    gte = "__ge__"
    lte = "__le__"
    in_ = "in_"
    startswith = "startswith"
    endswith = "endswith"
    between = "between"
    like = "like"
    ilike = "ilike"
    contains = "contains"
    icontains = "icontains"
    not_eq = "__ne__"
    not_in = "not_in"
    not_like = "not_like"
    not_between = "not_between"
