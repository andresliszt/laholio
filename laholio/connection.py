"""Configuración para conectarse a Elasticsearch."""
# -*- coding: utf-8 -*-

from ssl import create_default_context

import certifi
from elasticsearch import Elasticsearch
from elasticsearch.transport import Transport
from elasticsearch_async.transport import AsyncTransport
from elasticsearch_dsl import connections

from laholio import S
from laholio.exceptions import ElasticsearchNotReady

CA_CERTS = certifi.where()


class ElasticSearchConnection:
    """Conexión a ES.

    Soporta dos tipos de conexiones. La primera, es la conexión clásica usada
    en la librería `elasticsearch-py`, la cual usa una clase de transporte que
    soporta métodos sincrónicos. La segunda, corresponde a una conexión usando
    unaclase de transporte que soporta llamadas asincrónicas, construida
    en la librería `elasticsearch-async`. La manera de declarar que tipo de
    conexión se usará, es a través del parámetro `transport_type`
    (sync o async).

    Ambas librerías son oficiales.

    Ver mas:
        elasticsearch-py:
            `https://elasticsearch-py.readthedocs.io/en/master/`

        elasticsearch-async:
            `https://github.com/elastic/elasticsearch-py-async`

    """

    def __init__(self, alias="default", transport_type="sync", **kwargs):

        if transport_type not in ("sync", "async"):
            raise ValueError("`transport_type` debe ser `sync` o `async`")

        if S.ELASTICSEARCH_USER and S.ELASTICSEARCH_PASSWORD:
            kwargs.update(
                **dict(
                    http_auth=(
                        S.ELASTICSEARCH_USER,
                        S.ELASTICSEARCH_PASSWORD.get_secret_value(),
                    ),
                    scheme="https",
                )
            )

        if S.ELASTICSEARCH_SSL_CERT_PATH:

            context = create_default_context(
                cafile=S.ELASTICSEARCH_SSL_CERT_PATH
            )
            kwargs.update(**dict(ssl_context=context))

        kwargs.setdefault("alias", alias)
        kwargs.setdefault("hosts", [S.ELASTICSEARCH_HOST])
        kwargs.setdefault("verify_certs", True)
        kwargs.setdefault("ca_certs", CA_CERTS)
        kwargs.setdefault(
            "transport_class",
            AsyncTransport if transport_type == "async" else Transport,
        )

        self._kwargs = kwargs  # pylint: disable=unused-argument
        self._connection = None

    def index_names(self):
        """Nombre de indices  asociados a la conexión."""
        return list(self.connection.indices.get("*").keys())

    @property
    def connection(self) -> Elasticsearch:
        """Conexión a Elasticsearch."""

        if self._connection is None:
            self._connection = connections.create_connection(**self._kwargs)
        return self._connection

    def test_connection(self):
        """Prueba si el cluster está arriba."""
        return self.connection.ping()

    def verify_index_exist(self, index_name: str):
        """Verifica si un índice existe."""
        if self.connection.indices.exists(index_name):
            return True
        return False

    def raise_unconnected(self):
        """Bota el programa si es que el cluster está abajo."""
        if not self.connection.ping():
            raise ElasticsearchNotReady
