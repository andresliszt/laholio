# -*- coding: utf-8 -*-
"""Prueba buscador filtro por proveedor"""


import time

import pytest

from . import SkuTest
from . import SkuSearchTest
from . import ASYNC_CONN
from . import SYNC_CONN
from . import SkuInsertTest

def setup_module(module):

    if not SYNC_CONN.indices.exists(index="test_index"):
        SkuTest.init(using=SYNC_CONN)

    documents = (
        SkuTest(sku_id=1, descripcion_corta="test", rut_proveedor_=1),
        SkuTest(sku_id=2, descripcion_corta="test", rut_proveedor_=2),
        SkuTest(sku_id=3, descripcion_corta="test", rut_proveedor_=3),
        SkuTest(sku_id=4, descripcion_corta="test", rut_proveedor_=4),
    )

    inserter = SkuInsertTest(connection=SYNC_CONN)

    inserter.bulk_request(documents)

    SkuTest._index.refresh()


def teardown_module(module):
    SYNC_CONN.indices.delete(index="test_index")


@pytest.mark.parametrize(
    "rut, len_results",
    [(None, 4), (1, 1), ([1, 2], 2), ([1, 2, 3], 3), ([2, 1, 4, 3], 4)],
)

@pytest.mark.asyncio
async def test_filter_by_provider(rut, len_results):
    crud = SkuSearchTest(connection=ASYNC_CONN)

    results = await crud.search_product("test", rut_proveedor_=rut)

    assert len(results) == len_results
