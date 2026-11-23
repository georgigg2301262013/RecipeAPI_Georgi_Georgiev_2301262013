from pydantic import BaseModel, Field, ConfigDict, EmailStr, field_validator
from enums import Unit


#removes the spaces at the beginning and at the end and checks that the text is not empty
def check_not_blank(value: str, field_name: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError(f"{field_name} can not be empty")
    return value


#Author

class Author(BaseModel):
    #Setting model_config to ConfigDict(from_attributes=True) tells pydantic to use attributes (with getattr) to
    #initialize instead of expecting dictionary
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr


class CreateAuthor(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr

    @field_validator("name")
    @classmethod
    def validate_name(cls, name):
        return check_not_blank(name, "Name")

class UpdateAuthor(CreateAuthor):
    pass


#Category

class Category(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class CreateCategory(BaseModel):
    name: str = Field(min_length=1, max_length=100)

    @field_validator("name")
    @classmethod
    def validate_name(cls, name):
        return check_not_blank(name, "Name")

class UpdateCategory(CreateCategory):
    pass


#Ingredient

class Ingredient(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class CreateIngredient(BaseModel):
    name: str = Field(min_length=1, max_length=100)

    @field_validator("name")
    @classmethod
    def validate_name(cls, name):
        return check_not_blank(name, "Name")

class UpdateIngredient(CreateIngredient):
    pass


#Recipe

class Recipe(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    instructions: str
    prep_time: int
    servings: int
    author_id: int
    category_id: int | None


class CreateRecipe(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    instructions: str = Field(min_length=1)
    prep_time: int = Field(gt=0) #preparation time in minutes, positive integer
    servings: int = Field(gt=0)
    author_id: int
    category_id: int | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, title):
        return check_not_blank(title, "Title")

    @field_validator("instructions")
    @classmethod
    def validate_instructions(cls, instructions):
        return check_not_blank(instructions, "Instructions")

class UpdateRecipe(CreateRecipe):
    pass


#Ingredients in a recipe (association)

class RecipeIngredient(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ingredient: Ingredient
    quantity: float
    unit: Unit


class AddRecipeIngredient(BaseModel):
    ingredient_id: int
    quantity: float = Field(gt=0)
    unit: Unit


class UpdateRecipeIngredient(BaseModel):
    quantity: float = Field(gt=0)
    unit: Unit


#recipe with ingredient quantities recalculated for the requested number of servings
class ScaledRecipe(BaseModel):
    id: int
    title: str
    instructions: str
    prep_time: int
    author_id: int
    category_id: int | None
    original_servings: int
    servings: int
    ingredients: list[RecipeIngredient]