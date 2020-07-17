# -*- coding: utf-8 -*-
"""Prueba para el compaginador de :class: ´laholio.crud.SkuCRUD´"""
import pytest

from . import SkuTest
from . import SkuSearchTest
from . import SkuInsertTest
from . import SYNC_CONN
from . import ASYNC_CONN


def setup_module():
    if not SYNC_CONN.indices.exists(index="test_index"):
        SkuTest.init(using=SYNC_CONN)

    documents = []

    for i in range(20):
        documents.append(
            SkuTest(sku_id=i, descripcion_corta="descripción {}".format(i))
        )

    inserter = SkuInsertTest(connection=SYNC_CONN)

    inserter.bulk_request(documents)

    SkuTest._index.refresh()


def teardown_module():
    SYNC_CONN.indices.delete(index="test_index")

@pytest.mark.asyncio
async def test_compaginated_search_search_got_all_documents():
    """Si la búsqueda obtuvo todos los resultados, entonces no debiese

       estar habilitada la opción 'ver mas'."""

    searcher =  SkuSearchTest(connection=ASYNC_CONN)

    results = await searcher.search_product("descripcion", search_size=30)
    # Note que estamos buscando 30 documentos para un match de 20, debiese retornar 20.

    assert len(results) == 20 and searcher.last_search is None

@pytest.mark.asyncio
async def test_compaginated_search_search_got_part_of_all_documents():
    """Búsqueda con tamaño menor al total de matches, debiese habilitar 'ver mas'"""

    searcher = SkuSearchTest(connection=ASYNC_CONN)

    await searcher.search_product("descripcion", search_size=5)

    async for pag in searcher.see_more(pag_size=10):
        assert len(pag) == 10

@pytest.mark.asyncio
async def test_init_scroll_method():
    searcher = SkuSearchTest(connection=ASYNC_CONN)
    await searcher.search_product("descripcion", search_size= 5)
    results_1 , _id = await searcher.init_scroll(searcher.last_search, pag_size= 10)
    results_2, _id = await searcher.next_page(_id)
    results_3, _id = await searcher.next_page(_id)
    assert len(results_1) == 10 and len(results_2) == 10 and results_3 == [] 
