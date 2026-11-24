from exceptions import NotFound, DuplicationError
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from db.models import Recipe, RecipeIngredient
from services.author_service import AuthorService
from services.category_service import CategoryService
from services.ingredient_service import IngredientService

def get_recipe_service():
    return RecipeService()

class RecipeService:
    def _get(self, id: int, db_session: Session) -> Recipe:
        recipe = db_session.get(Recipe, id)
        if recipe is None:
            raise NotFound(f"Recipe with id {id} not found")
        return recipe

    #one author can not have two recipes with the same title (case-insensitive, without leading/trailing spaces)
    def _check_title(self, title: str, author_id: int, db_session: Session, exclude_id: int | None = None):
        stmt = select(Recipe).where(Recipe.author_id == author_id).where(
            func.lower(Recipe.title) == title.strip().lower())
        if exclude_id is not None:
            stmt = stmt.where(Recipe.id != exclude_id)
        if db_session.scalars(stmt).first() is not None:
            raise DuplicationError(
                f"Author with id {author_id} already has a recipe with title {title}")

    def _get_recipe_ingredient(self, recipe_id: int, ingredient_id: int, db_session: Session) -> RecipeIngredient | None:
        return db_session.scalars(
            select(RecipeIngredient)
            .where(RecipeIngredient.recipe_id == recipe_id)
            .where(RecipeIngredient.ingredient_id == ingredient_id)
        ).one_or_none()

    #CRUD

    #all filters are optional and are combined with AND
    def get_recipes(self, db_session: Session, title: str | None = None,
                    category_id: int | None = None, max_prep_time: int | None = None) -> list[Recipe]:
        stmt = select(Recipe)
        if title is not None and title.strip():
            #search by part of the title
            stmt = stmt.where(func.lower(Recipe.title).contains(title.strip().lower(), autoescape=True))
        if category_id is not None:
            stmt = stmt.where(Recipe.category_id == category_id)
        if max_prep_time is not None:
            stmt = stmt.where(Recipe.prep_time <= max_prep_time)
        return db_session.scalars(stmt).all()

    def get_recipe(self, id: int, db_session: Session) -> Recipe:
        return self._get(id, db_session)

    def create_recipe(self, data: dict, db_session: Session,
                      author_service: AuthorService, category_service: CategoryService) -> Recipe:
        author = author_service.get_author(data["author_id"], db_session)
        category = None
        if data["category_id"] is not None:
            category = category_service.get_category(data["category_id"], db_session)
        self._check_title(data["title"], author.id, db_session)

        recipe = Recipe(title=data["title"],
                        instructions=data["instructions"],
                        prep_time=data["prep_time"],
                        servings=data["servings"],
                        difficulty=data["difficulty"],
                        author=author,
                        category=category)
        db_session.add(recipe)
        db_session.commit()
        db_session.refresh(recipe)
        return recipe

    def update_recipe(self, id: int, data: dict, db_session: Session,
                      author_service: AuthorService, category_service: CategoryService) -> Recipe:
        recipe = self._get(id, db_session)
        author = author_service.get_author(data["author_id"], db_session)
        category = None
        if data["category_id"] is not None:
            category = category_service.get_category(data["category_id"], db_session)
        self._check_title(data["title"], author.id, db_session, exclude_id=id)

        recipe.title = data["title"]
        recipe.instructions = data["instructions"]
        recipe.prep_time = data["prep_time"]
        recipe.servings = data["servings"]
        recipe.difficulty = data["difficulty"]
        recipe.author = author
        recipe.category = category
        db_session.commit()
        db_session.refresh(recipe)
        return recipe

    def delete_recipe(self, id: int, db_session: Session):
        #the links to the ingredients are deleted (cascade), the ingredients stay
        recipe = self._get(id, db_session)
        db_session.delete(recipe)
        db_session.commit()

    #Ingredients of a recipe

    def get_recipe_ingredients(self, id: int, db_session: Session) -> list[RecipeIngredient]:
        #404 if the recipe does not exist, empty list if it has no ingredients
        self._get(id, db_session)
        return db_session.scalars(
            select(RecipeIngredient).where(RecipeIngredient.recipe_id == id)).all()

    def add_ingredient(self, id: int, data: dict, db_session: Session,
                       ingredient_service: IngredientService) -> RecipeIngredient:
        recipe = self._get(id, db_session)
        ingredient = ingredient_service.get_ingredient(data["ingredient_id"], db_session)
        #an ingredient can be added only once to a recipe, the existing quantity is not changed
        if self._get_recipe_ingredient(recipe.id, ingredient.id, db_session) is not None:
            raise DuplicationError(
                f"Ingredient with id {ingredient.id} is already added to recipe with id {recipe.id}")

        recipe_ingredient = RecipeIngredient(recipe=recipe,
                                             ingredient=ingredient,
                                             quantity=data["quantity"],
                                             unit=data["unit"])
        db_session.add(recipe_ingredient)
        db_session.commit()
        db_session.refresh(recipe_ingredient)
        return recipe_ingredient

    def update_ingredient(self, id: int, ingredient_id: int, data: dict, db_session: Session,
                          ingredient_service: IngredientService) -> RecipeIngredient:
        self._get(id, db_session)
        ingredient_service.get_ingredient(ingredient_id, db_session)
        recipe_ingredient = self._get_recipe_ingredient(id, ingredient_id, db_session)
        if recipe_ingredient is None:
            raise NotFound(f"Ingredient with id {ingredient_id} is not part of recipe with id {id}")

        recipe_ingredient.quantity = data["quantity"]
        recipe_ingredient.unit = data["unit"]
        db_session.commit()
        db_session.refresh(recipe_ingredient)
        return recipe_ingredient

    def remove_ingredient(self, id: int, ingredient_id: int, db_session: Session,
                          ingredient_service: IngredientService):
        #only the link is deleted, the ingredient itself stays
        self._get(id, db_session)
        ingredient_service.get_ingredient(ingredient_id, db_session)
        recipe_ingredient = self._get_recipe_ingredient(id, ingredient_id, db_session)
        if recipe_ingredient is None:
            raise NotFound(f"Ingredient with id {ingredient_id} is not part of recipe with id {id}")
        db_session.delete(recipe_ingredient)
        db_session.commit()

    #Recalculate servings

    def get_scaled_recipe(self, id: int, servings: int, db_session: Session) -> dict:
        recipe = self._get(id, db_session)
        factor = servings / recipe.servings

        #we build new data and do not change the ORM objects, so nothing is saved in the database
        ingredients = []
        for recipe_ingredient in recipe.recipe_ingredients:
            ingredients.append({
                "ingredient": recipe_ingredient.ingredient,
                "quantity": round(recipe_ingredient.quantity * factor, 2),
                "unit": recipe_ingredient.unit,
            })

        return {
            "id": recipe.id,
            "title": recipe.title,
            "instructions": recipe.instructions,
            "prep_time": recipe.prep_time,
            "difficulty": recipe.difficulty,
            "author_id": recipe.author_id,
            "category_id": recipe.category_id,
            "original_servings": recipe.servings,
            "servings": servings,
            "ingredients": ingredients,
        }