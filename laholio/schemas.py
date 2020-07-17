# -*- coding: utf-8 -*-
"""Definición de documento Sku."""
from enum import Enum

from elasticsearch import Elasticsearch
from elasticsearch_dsl.document import \
    IndexMeta  # pylint: disable=no-name-in-module
from elasticsearch_dsl.document import InnerDoc

from laholio import S
from laholio.analyzers import INDEX_ANALYZER_DESCRIPTION
from laholio.analyzers import INDEX_ANALYZER_SKU
from laholio.analyzers import SEARCH_ANALYZER
from laholio.analyzers import SUGGESTER_ANALYZER_DESCRIPTION
from laholio.utils._elasticsearch import Document
from laholio.utils._elasticsearch import EnumText
from laholio.utils._fields import Boolean  # pylint: disable=no-name-in-module
from laholio.utils._fields import Integer  # pylint: disable=no-name-in-module
from laholio.utils._fields import Keyword  # pylint: disable=no-name-in-module
from laholio.utils._fields import Nested  # pylint: disable=no-name-in-module
from laholio.utils._fields import Object  # pylint: disable=no-name-in-module
from laholio.utils._fields import Text  # pylint: disable=no-name-in-module


class SkuQualityStatus(Enum):
    """Enum class sobre la info del sku."""

    completo = "Completo"
    """Contiene todos los datos requeridos definidos en :class:`~Sku`"""
    incompleto = "Incompleto"


class CatalogoQualityStatus(Enum):
    """Enum class sobre el estado global de la carga de catálogo."""

    completo = "Completo"
    """Toda fila del cátalogo fue cargado exitosamente."""

    incompleto = "Incompleto"
    """Algunas filas del catálogo fue cargado exitosamente."""

    extension_invalida = "Extensión inválida"
    """El archivo no es un excel válido."""

    columnas_incorrectas = "Columnas del Excel no corresponden"
    """Excel válido, pero sus columnas no son las correctas."""

    en_proceso = "En proceso"


class Sku(Document):
    """Definición documento Sku."""

    sku_id = Text(required=True, description="Id del almacenamiento")
    sku = Text(
        required=True,
        analyzer=INDEX_ANALYZER_SKU,
        search_analyzer=SEARCH_ANALYZER,
        description="Stock Keeping Unit: "
        "Identificador único del producto, definido por el vendedor",
    )
    sku_fabricante = Text(
        analyzer=INDEX_ANALYZER_SKU,
        search_analyzer=SEARCH_ANALYZER,
        description="Stock Keeping Unit: "
        "Identificador único del producto, definido por el fabricante",
    )
    dv_proveedor = Text(required=True)
    dv_fabricante = Text()
    rut_proveedor_ = Integer(
        required=True, description="RUT sin digito verificador"
    )
    rut_fabricante_ = Integer(description="RUT sin digito verificador")
    contenido = Text(required=True)
    formato_venta = Text(required=True)
    unidad_medida = Text(required=True)
    descripcion_corta = Text(
        required=True,
        analyzer=INDEX_ANALYZER_DESCRIPTION,
        search_analyzer=SEARCH_ANALYZER,
    )

    descripcion_larga = Text()
    atributos = Object(
        dynamic=True, required=True
    )  # attributos como dynamic mapping, pues los atributos varian por sku

    imagenes = Object(
        required=True,
        dynamic="strict",
        properties={"normal": Text(), "miniatura": Text()},
    )

    descripcion_corta_ = Text(
        required=True,
        analyzer=SUGGESTER_ANALYZER_DESCRIPTION,
        search_analyzer=SUGGESTER_ANALYZER_DESCRIPTION,
    )
    # TODO: HACER QUE ESTE CAMPO SE LLENE AUTOMATICAMENTE USANDO
    # descripcion_corta, y no dejar que este se cargue por si solo!

    especificaciones = Object(
        dynamic="strict",
        properties={"ficha_tecnica": Text(), "url_fabricante": Text()},
    )

    status = EnumText(required=True, enum_class=SkuQualityStatus)

    class Index:  # pylint: disable=too-few-public-methods
        """Index catálogo."""

        name = S.CATALOGO_INDEX_NAME
        settings = {"number_of_shards": 1, "number_of_replicas": 0}

    def save(
        self, **kwargs
    ):  # pylint: disable=W0221 # https://github.com/PyCQA/pylint/pull/3001
        """Override el método save para generar custom id."""
        if (
            self.sku_id is None
        ):  # No se permitirán skus con id generado aleatorio
            raise ValueError("El campo sku_id es obligatorio")
        self.meta.id = self.sku_id
        return super().save(**kwargs)

    def to_dict_with_custom_id(self, **kwargs):
        """Override el método to_dict para agragar el _id field.

        cuando se instancia un objeto de :class: .Sku, el método
        to_dict no incorpora el meta field `_id`, pues este es creado al
        momento de guardar el dato. Agregar el `_id` field antes del guardado
        permite la carga de documentos con `_id` propio usando el método
        :meth: `elasticsearch.helpers.bulk`.

        Usar solo para bulk insert!

        """
        if (
            self.sku_id is None
        ):  # No se permitirán skus con id generado aleatorio
            raise ValueError("El campo sku_id es obligatorio")

        d = super().to_dict(**kwargs)
        d["_id"] = self.sku_id
        return d

    @staticmethod
    def build_sku_id(rut_proveedor_: int, sku: str):
        return "_".join((str(rut_proveedor_), str(sku)))


class SkuYellow(Sku):
    """Clase auxiliar para transformar a pydantic con campos más relajados."""

    contenido = Text(required=False)
    formato_venta = Text(required=False)
    unidad_medida = Text(required=False)
    atributos = Object(
        dynamic=True, required=False
    )  # attributos como dynamic mapping, pues los atributos varian por sku

    imagenes = Object(
        required=False,
        dynamic="strict",
        properties={"normal": Text(), "miniatura": Text()},
    )

    class Index:  # pylint: disable=R0903
        """Sobre escribe el Index heredado por Sku."""


class TypeSkuError(Enum):
    """Tipos de errores para el Sku."""

    fatal = "Fatal"
    """Si no tiene al menos la info requerida de :class: `~SkuYellow`"""
    missing = "Falta información"


class SkuErrors(InnerDoc):
    """Info de errores de un Sku dado."""

    row = Integer(required=True)
    """fila del excel donde está el sku erroneo"""
    sku_errors = Text(required=True)
    """string json con el detalle del error"""
    type_error = EnumText(enum_class=TypeSkuError)


class CatalogoUpload(Document):
    """Documento del status del catálogo subido."""

    client_id = Keyword(required=True)
    rut_proveedor = Keyword(required=True)
    file_hash = Keyword(required=True)
    status = EnumText(required=True, enum_class=CatalogoQualityStatus)
    incomplete_errors = Nested(SkuErrors)
    fatal_errors = Nested(SkuErrors)

    class Index:  # pylint: disable=too-few-public-methods
        """Index para el status de la carga de excel de catalogos."""

        name = "catalogo_upload"
        settings = {"number_of_shards": 1, "number_of_replicas": 0}

    def to_dict_with_custom_id(self, **kwargs):
        """Override el método to_dict para agragar el _id field.

        cuando se instancia un objeto de :class: .Sku, el método
        to_dict no incorpora el meta field `_id`, pues este es creado al
        momento de guardar el dato. Agregar el `_id` field antes del guardado
        permite la carga de documentos con `_id` propio usando el método
        :meth: `elasticsearch.helpers.bulk`.

        Usar solo para bulk insert!

        TODO: mover metodo a clase padre e implementar abtract property

        """
        if (
            self.file_hash is None
        ):  # No se permitirán uploads con id generado aleatorio
            raise ValueError("El campo file_hash es obligatorio")

        d = super().to_dict(**kwargs)
        d["_id"] = self.file_hash
        return d


class SkuCopy(Sku):  # pylint: disable=R0903
    """Copia documento Sku."""

    class Index:  # pylint: disable=R0903
        """Index catálogo de copia.

        Para pruebas

        """

        name = "catalgo_copy"
        settings = {"number_of_shards": 1, "number_of_replicas": 0}


def init_schema(connection: Elasticsearch, doc: IndexMeta = Sku, **meta_kw):
    """Construye el indice y los mappings si aún no existen.

    Args:
        connection : Conexión a ES
        doc: Doc asociado al índice por crear.

    meta_kw:

        extra meta fields para la creación del índice. Ejemplo:
            meta_kw = {"dynamic" = True}

    """

    if not connection.indices.exists(doc.Index.name):
        meta_kw.setdefault("dynamic", "strict")
        doc.extra_meta_field(**meta_kw)
        doc.init(using=connection)


def put_alias():
    """Implemntar puesta de alias en un índice ya existente."""
