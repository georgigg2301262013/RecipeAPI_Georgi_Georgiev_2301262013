from enum import Enum


#allowed units for the quantity of an ingredient in a recipe
class Unit(str, Enum):
    g = "g"
    ml = "ml"
    pcs = "pcs"