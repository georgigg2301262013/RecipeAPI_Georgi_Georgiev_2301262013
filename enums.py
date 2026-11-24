from enum import Enum


#allowed units for the quantity of an ingredient in a recipe
class Unit(str, Enum):
    g = "g"
    ml = "ml"
    pcs = "pcs"
   
#difficulty level of a recipe
class Difficulty(str, Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"