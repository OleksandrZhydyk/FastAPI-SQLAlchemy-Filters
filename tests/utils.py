from enum import Enum


class JobCategory(str, Enum):
    finance = "Finance"
    marketing = "Marketing"
    agro = "Agriculture"
    it = "IT"
    metallurgy = "Metallurgy"
    medicine = "Medicine"
    construction = "Construction"
    building = "Building"
    services = "Services"
    miscellaneous = "Miscellaneous"
