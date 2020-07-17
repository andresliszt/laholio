"""Laholio Settings.

Set any and all project variables here.

If you have two version of the project running, they should differ only
in variables set in this file.

Optionally, secret stuff is located in the a .env file, automatically
loaded by :mod:`pydantic` here.

"""
from typing import Optional

from petri.loggin import LogFormatter
from petri.loggin import LogLevel
from petri.settings import BaseSettings
from pydantic.types import SecretStr


class Settings(BaseSettings):
    """Valores comunes definidos aquí.

    Por defecto BaseSettings considera valores de campos en la siguiente
    prioridad (donde 3. tiene la mayor prioridad y sobreescribe las
    dos):

    1. Valores por defecto en la Config Class (pydantic).
    2. Variables de entorno.
    3. Argumentos pasados en instanciación de clase.

    .. Ver::

        https://pydantic-docs.helpmanual.io/#settings

    """

    ELASTICSEARCH_HOST: str
    """Host for elasticsearch server"""

    ELASTICSEARCH_USER: Optional[str] = None

    ELASTICSEARCH_PASSWORD: Optional[SecretStr] = None

    ELASTICSEARCH_SSL_CERT_PATH: Optional[str] = None

    CATALOGO_INDEX_NAME: str
    """Nombre que define el índice del catálogo"""
    # TODO: Agregar validador en pydantic para que el nombre sea valido
    # en es. No cualquier nombre es permitido en es, y ademas cuando uno
    # escribe A-B, en es se guarda como A_B. Ver una manera de escribir
    # nombres.


class Production(Settings):
    """Valores específicos de producción."""

    LOG_FORMAT = LogFormatter.JSON
    LOG_LEVEL = LogLevel.TRACE


class Development(Settings):
    """Valores específicos de desarrollo."""

    LOG_FORMAT = LogFormatter.COLOR  # requires colorama
    LOG_LEVEL = LogLevel.INFO
