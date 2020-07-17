"""Exceptions and Error Handling."""

import abc
from typing import Any


class LaholioErrorMixin(abc.ABC, BaseException):
    """Base class for ic analytics errors and exceptions.

    Example:

        >>> class MyError(LaholioErrorMixing, NameError):
                msg_template = "Value ``{value}`` could not be found"
        >>> raise MyError(value="can't touch this")
        (...)
        MyError: Value `can't touch this` could not be found

    """

    @property
    @abc.abstractmethod
    def msg_template(self) -> str:
        """A template to print when the exception is raised.

        Example:
            "Value ``{value}`` could not be found"

        """

    def __init__(self, **ctx: Any) -> None:
        self.ctx = ctx
        super().__init__()

    def __str__(self) -> str:
        txt = self.msg_template
        for name, value in self.ctx.items():
            txt = txt.replace("{" + name + "}", str(value))
        txt = txt.replace("`{", "").replace("}`", "")

        return txt


class ElasticsearchNotReady(LaholioErrorMixin, NameError):
    """Levantar cuando el host(s) de es no este activo."""

    msg_template = "Elasticsearch no esta listo."


class NotUsingEsConnection(LaholioErrorMixin, NameError):
    """Levantar cuando se intenta operar no estando conectado a es."""

    msg_template = "Se intenta operar no estando ligado a una conexión de es."


class NotUsingIndex(LaholioErrorMixin, NameError):
    """Levantar cuando se intenta operar no estando asociado a un índice."""

    msg_template = "Se intenta operar fuera sin un índice asociado"


class IndexNotExists(LaholioErrorMixin, NameError):
    """Levantar cuando se intente operar en un índice de es no creado."""

    msg_template = "El índice `{index}` no existe."


class NotAsyncEsConnection(LaholioErrorMixin, NameError):
    """Levantar cuando se use conexión  no asíncrona en métodos asíncronos."""

    msg_template = "La conexión `{connection}` no es asíncrona."
