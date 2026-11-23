class AppError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

#the requested resource does not exist -> 404
class NotFound(AppError):
    pass

#a resource with the same unique value already exists -> 409
class DuplicationError(AppError):
    pass

#the operation breaks a business rule (e.g. deleting an author with recipes) -> 409
class ConflictError(AppError):
    pass