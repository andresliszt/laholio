# -*- coding: utf-8 -*-
"""Define ensure_index_exists, para decorar cualquier funcion."""

from functools import wraps

from laholio.connection import ElasticSearchConnection
from laholio.schemas import init_schema


def ensure_index_exists(func):
    """Decorador para asegurar que el índice existe."""

    @wraps(func)
    def wrapped(*args, **kwargs):

        init_schema(connection=ElasticSearchConnection().connection)

        return func(*args, **kwargs)

    return wrapped
