from exceptions import NotFound, DuplicationError, ConflictError
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from db.models import Author, Recipe

def get_author_service():
    return AuthorService()

class AuthorService:
    def _get(self, id: int, db_session: Session) -> Author:
        author = db_session.get(Author, id)
        # if no author found in database throw exception
        if author is None:
            raise NotFound(f"Author with id {id} not found")
        return author

    #different authors can have the same name, but the email must be unique (case-insensitive)
    def _check_email(self, email: str, db_session: Session, exclude_id: int | None = None):
        stmt = select(Author).where(func.lower(Author.email) == email.strip().lower())
        if exclude_id is not None:
            stmt = stmt.where(Author.id != exclude_id)
        if db_session.scalars(stmt).first() is not None:
            raise DuplicationError(f"Author with email {email} already exists")

    def get_authors(self, db_session: Session) -> list[Author]:
        return db_session.scalars(select(Author)).all()

    def get_author(self, id: int, db_session: Session) -> Author:
        return self._get(id, db_session)

    def get_author_recipes(self, id: int, db_session: Session) -> list[Recipe]:
        #404 if the author does not exist, empty list if the author has no recipes
        self._get(id, db_session)
        return db_session.scalars(select(Recipe).where(Recipe.author_id == id)).all()

    def create_author(self, data: dict, db_session: Session) -> Author:
        self._check_email(data["email"], db_session)
        author = Author(name=data["name"], email=data["email"])
        db_session.add(author)
        db_session.commit()
        db_session.refresh(author)
        return author

    def update_author(self, id: int, data: dict, db_session: Session) -> Author:
        author = self._get(id, db_session)
        self._check_email(data["email"], db_session, exclude_id=id)
        author.name = data["name"]
        author.email = data["email"]
        db_session.commit()
        db_session.refresh(author)
        return author

    def delete_author(self, id: int, db_session: Session):
        author = self._get(id, db_session)
        #the author can not be deleted while he has recipes
        has_recipes = db_session.scalars(
            select(Recipe).where(Recipe.author_id == id)).first() is not None
        if has_recipes:
            raise ConflictError(f"Author with id {id} has recipes and can not be deleted")
        db_session.delete(author)
        db_session.commit()