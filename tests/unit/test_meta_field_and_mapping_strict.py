# -*- coding: utf-8 -*-

import pytest

from . import SkuTest
from . import SkuSearchTest
from .import SkuInsertTest
from . import SYNC_CONN

from laholio.schemas import init_schema
from laholio.schemas import SkuQualityStatus

def setup_module(module):
    init_schema(SYNC_CONN, doc=SkuTest)


def teardown_module(module):
    SYNC_CONN.indices.delete(index="test_index")


def test_correct_meta_id_field():
    """Prueba para verificar el metafield `_id`

    Se sobrecargó el metafield `_id`en :class:~`laholio.schemas.Sku` por
    el field `sku_id`. Con esta prueba se verifica si es que este último
    field funciona verdaderamente como el meta `_id`"""

    sku = SkuTest(
        sku_id=1,
        sku="test",
        rut_proveedor_=1,
        dv_proveedor="test",
        descripcion_corta="test",
        descripcion_corta_ = "test",
        atributos={"test": "test"},
        imagenes={"normal": "test", "miniatura": "test"},
        status= SkuQualityStatus.completo.value,
        contenido= "test",
        formato_venta = "test",
        unidad_medida = "test",
    )

    sku.save()

    assert SkuTest.get(id=1)


def test_strict_index_mapping_using_save_method():
    """Prueba para verificar que el índice esta en modo estricto

    No se permiten campos que no sean los que están definidos en 

    :class:`~laholio.schemas.Sku`
    
    """
    from elasticsearch.exceptions import RequestError

    fake_sku = SkuTest(
        sku_id=1,
        sku="test",
        rut_proveedor_=1,
        dv_proveedor="test",
        descripcion_corta="test",
        descripcion_corta_ = "test",
        atributos={"test": "test", "test_": "test", "test__": "test"},
        imagenes={"normal": "test", "miniatura": "test"},
        fake_field="fake test",
        status=SkuQualityStatus.completo.value,
        contenido= "test",
        formato_venta = "test",
        unidad_medida = "test",
    )

    with pytest.raises(RequestError):

        assert fake_sku.save()


def test_strict_index_mapping_using_bulk_insert_method():
    """Prueba para verificar que el índice esta en modo estricto

    No se permiten campos que no sean los que están definidos en 

    :class:`~laholio.schemas.Sku`. En esta prueba se usa el método

    :func: `laholio.crud.SkuCRUD.bulk_request`, el cual no está pensado

    para botar el programa si es que hay una falla (Solo reporta el documento
    
    que falla). Debería no cargarse el documento que se intenta indexar

    con un campo falso.
    
    """

    from elasticsearch.exceptions import NotFoundError

    fake_sku = SkuTest(
        sku_id=10,
        sku="test",
        sku_fabricante="test",
        rut_proveedor_=1,
        dv_proveedor="test",
        descripcion_corta="test",
        atributos={"test": "test"},
        imagenes={"normal": "test", "miniatura": "test"},
        fake_field="fake test",
    )

    inserter = SkuInsertTest(SYNC_CONN)

    inserter.bulk_request([fake_sku])

    with pytest.raises(NotFoundError):

        assert SkuTest.get(id=10)
