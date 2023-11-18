from flask_restful import abort

from models.db_session import create_session


def abort_if_doesnt_exist(field_name, model):
    def decorator(func):
        def wrapper(*args, **kwargs):
            with create_session() as db:
                if db.get(model, kwargs[field_name]) is None:
                    abort(404,
                          message=f"The {field_name} with value: {kwargs[field_name]} doesn't exist in the database.")
            return func(*args, **kwargs)

        return wrapper

    return decorator
