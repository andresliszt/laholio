# -*- coding: utf-8 -*-
"""Pruebas unitarias para laholio"""

from .conftest import ASYNC_CONN
from .conftest import SYNC_CONN
from laholio.schemas import Sku
from laholio.crud import SkuSearch
from laholio.crud import BulkInsertUpdateDelete


class SkuTest(Sku):
    """Documento de prueba indexado a el indice de prueba"""

    class Index(Sku.Index):
        """Misma configuración que Sku, pero diferente indice"""

        name = "test_index"


class SkuSearchTest(SkuSearch):
    """Sobreescribe  :class:`laholio.crud.SkuSearch`"""

    def __init__(self, connection):
        super().__init__(connection)
        self.index_name = SkuTest.Index.name


class SkuInsertTest(BulkInsertUpdateDelete):
    """Sobreescribe  :class:`laholio.crud.Insert`"""

    def __init__(self, connection):
        super().__init__(connection, SkuTest.Index.name)

