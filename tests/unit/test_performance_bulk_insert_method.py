# -*- coding: utf-8 -*-

import random

import pytest

from . import SkuTest
from . import SkuSearchTest
from . import SkuInsertTest
from . import SYNC_CONN
from . import ASYNC_CONN
from laholio.connection import ElasticSearchConnection

CANTIDAD_DE_DOCUMENTOS_A_CARGAR_USANDO_DSL = int(1e2)
CANTIDAD_DE_DOCUMENTOS_A_CARGAR_USANDO_RAW = int(1e2)


def setup_module(module):

    if not SYNC_CONN.indices.exists(index="test_index"):
        SkuTest.init(using=SYNC_CONN)

    documents_dsl = (
        SkuTest(sku_id=i, descripcion_corta="descripcion {}".format(i))
        for i in range(1, CANTIDAD_DE_DOCUMENTOS_A_CARGAR_USANDO_DSL)
    )

    documents_raw = (
        SkuTest(
            sku_id=i, descripcion_corta="descripcion {}".format(i)
        ).to_dict_with_custom_id(include_meta=True)
        for i in range(
            CANTIDAD_DE_DOCUMENTOS_A_CARGAR_USANDO_DSL,
            CANTIDAD_DE_DOCUMENTOS_A_CARGAR_USANDO_DSL
            + CANTIDAD_DE_DOCUMENTOS_A_CARGAR_USANDO_RAW+ 1,
        )
    )

    inserter = SkuInsertTest(SYNC_CONN)

    inserter.bulk_request(documents_dsl, with_ids= True)

    inserter.bulk_request(documents_raw, document_type="raw", with_ids= True)

    SkuTest._index.refresh()


def teardown_module(module):

    SYNC_CONN.indices.delete(index="test_index")


@pytest.mark.asyncio
async def test_todos_los_sku_cargados():

    searcher = SkuSearchTest(ASYNC_CONN)

    search = searcher.search_base

    count = await search.count()

    assert (
        count
        == CANTIDAD_DE_DOCUMENTOS_A_CARGAR_USANDO_DSL
        + CANTIDAD_DE_DOCUMENTOS_A_CARGAR_USANDO_RAW
        
    )


RANDOM_IDS = [
    random.randint(
       1 ,
        CANTIDAD_DE_DOCUMENTOS_A_CARGAR_USANDO_DSL
        + CANTIDAD_DE_DOCUMENTOS_A_CARGAR_USANDO_RAW,
    )
    for i in range(1, 100)
]

TEST_DATA = [(_id, "descripcion {}".format(_id)) for _id in RANDOM_IDS]




@pytest.mark.parametrize("input_id, expected", TEST_DATA)
@pytest.mark.asyncio
async def test_productos_bien_cargados(input_id, expected):

    searcher = SkuSearchTest(ASYNC_CONN)

    search = searcher.search_base

    search = search.query("match", sku_id=input_id)

    response = await search.execute()

    descripcion = [hit.descripcion_corta for hit in response]

    assert len(descripcion) == 1 and descripcion[0] == expected
