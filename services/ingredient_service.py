from exceptions import NotFound, DuplicationError, ConflictError
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from db.models import Ingredient, RecipeIngredient

def get_ingredient_service():
    return IngredientService()

class IngredientService:
    def _get(self, id: int, db_session: Session) -> Ingredient:
        ingredient = db_session.get(Ingredient, id)
        if ingredient is None:
            raise NotFound(f"Ingredient with id {id} not found")
        return ingredient

    #the name must be unique (case-insensitive, without leading/trailing spaces)
    def _check_name(self, name: str, db_session: Session, exclude_id: int | None = None):
        stmt = select(Ingredient).where(func.lower(Ingredient.name) == name.strip().lower())
        if exclude_id is not None:
            stmt = stmt.where(Ingredient.id != exclude_id)
        if db_session.scalars(stmt).first() is not None:
            raise DuplicationError(f"Ingredient with name {name} already exists")

    def get_ingredients(self, db_session: Session) -> list[Ingredient]:
        return db_session.scalars(select(Ingredient)).all()

    def get_ingredient(self, id: int, db_session: Session) -> Ingredient:
        return self._get(id, db_session)

    def create_ingredient(self, data: dict, db_session: Session) -> Ingredient:
        self._check_name(data["name"], db_session)
        ingredient = Ingredient(name=data["name"])
        db_session.add(ingredient)
        db_session.commit()
        db_session.refresh(ingredient)
        return ingredient

    def update_ingredient(self, id: int, data: dict, db_session: Session) -> Ingredient:
        ingredient = self._get(id, db_session)
        self._check_name(data["name"], db_session, exclude_id=id)
        ingredient.name = data["name"]
        db_session.commit()
        db_session.refresh(ingredient)
        return ingredient

    def delete_ingredient(self, id: int, db_session: Session):
        ingredient = self._get(id, db_session)
        #the ingredient can not be deleted while it is used in a recipe
        is_used = db_session.scalars(
            select(RecipeIngredient).where(RecipeIngredient.ingredient_id == id)).first() is not None
        if is_used:
            raise ConflictError(f"Ingredient with id {id} is used in a recipe and can not be deleted")
        db_session.delete(ingredient)
        db_session.commit()