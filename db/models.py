from typing import Optional
from db.database import Base
from enums import Unit
from sqlalchemy import ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Author(Base):
    __tablename__ = "author"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)

    #passive_deletes="all" - the ORM does not touch the recipes when the author is deleted,
    #the database (ON DELETE RESTRICT) refuses the delete if the author has recipes
    recipes: Mapped[list["Recipe"]] = relationship(back_populates="author", passive_deletes="all")


class Category(Base):
    __tablename__ = "category"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)

    #the database sets recipe.category_id to NULL (ON DELETE SET NULL)
    recipes: Mapped[list["Recipe"]] = relationship(back_populates="category", passive_deletes=True)


class Ingredient(Base):
    __tablename__ = "ingredient"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)

    #the database (ON DELETE RESTRICT) refuses the delete if the ingredient is used in a recipe
    recipe_ingredients: Mapped[list["RecipeIngredient"]] = relationship(
        back_populates="ingredient", passive_deletes="all")


class Recipe(Base):
    __tablename__ = "recipe"
    #one author can not have two recipes with the same title
    __table_args__ = (
        UniqueConstraint("author_id", "title", name="uq_recipe_author_title"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    instructions: Mapped[str]
    prep_time: Mapped[int]
    servings: Mapped[int]
    author_id: Mapped[int] = mapped_column(ForeignKey("author.id", ondelete="RESTRICT"))
    category_id: Mapped[int | None] = mapped_column(ForeignKey("category.id", ondelete="SET NULL"))

    author: Mapped["Author"] = relationship(back_populates="recipes")
    category: Mapped[Optional["Category"]] = relationship(back_populates="recipes")
    #when a recipe is deleted, its links to the ingredients are deleted too (not the ingredients)
    recipe_ingredients: Mapped[list["RecipeIngredient"]] = relationship(
        back_populates="recipe", cascade="all, delete-orphan", passive_deletes=True)


#association model for the many-to-many relationship between Recipe and Ingredient
class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredient"
    __table_args__ = (
        #one ingredient can be added only once to a recipe
        UniqueConstraint("recipe_id", "ingredient_id", name="uq_recipe_ingredient"),
        CheckConstraint("quantity > 0", name="ck_recipe_ingredient_quantity_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipe.id", ondelete="CASCADE"))
    ingredient_id: Mapped[int] = mapped_column(ForeignKey("ingredient.id", ondelete="RESTRICT"))
    quantity: Mapped[float]
    unit: Mapped[Unit]

    recipe: Mapped["Recipe"] = relationship(back_populates="recipe_ingredients")
    ingredient: Mapped["Ingredient"] = relationship(back_populates="recipe_ingredients")