# -*- coding: utf-8 -*-
"""Tests for laholio.crud module."""
import csv
from pathlib import Path

import pytest

from tests.unit import SYNC_CONN
from tests.unit import ASYNC_CONN
from tests.unit import SkuTest
from tests.unit import SkuSearchTest
from tests.unit import SkuInsertTest

def setup_module(module):

    if not SYNC_CONN.indices.exists(index="test_index"):
        SkuTest.init(using=SYNC_CONN)

    documents = [
        SkuTest(
            sku_id=1,
            rut_proveedor_=76350871,
            descripcion_corta="Arena MELON ARIDOS Unidad",
            sku="A10N",
            descripcion_corta_="Arena MELON ARIDOS Unidad",
        ),
        SkuTest(
            sku_id=2,
            rut_proveedor_=76350871,
            descripcion_corta="Arena CBB Semi Industrial Unidad",
            descripcion_corta_="Arena CBB Semi Industrial Unidad",
            sku="203421",
        ),
        SkuTest(
            sku_id=3,
            rut_proveedor_=76350871,
            descripcion_corta="Grava MELON ARIDOS Normal Unidad",
            descripcion_corta_="Grava MELON ARIDOS Normal Unidad",
            sku="203496",
        ),
        SkuTest(
            sku_id=4,
            rut_proveedor_=76350871,
            descripcion_corta="Grava MELON ARIDOS Seca Unidad",
            descripcion_corta_="Grava MELON ARIDOS Seca Unidad",
            sku="G40N",
        ),
        SkuTest(
            sku_id=5,
            rut_proveedor_=76350871,
            descripcion_corta="Cemento CBB Especial Unidad",
            descripcion_corta_="Cemento CBB Especial Unidad",
            sku="200032",
        ),
        SkuTest(
            sku_id=6,
            descripcion_corta="Hormigón Preparado AISLANTES NACIONALES Bolsa 25 kg",
            descripcion_corta_="Hormigón Preparado AISLANTES NACIONALES Bolsa 25 kg",
            sku="BMBEHM2025",
        ),
        SkuTest(
            sku_id=7,
            descripcion_corta="Cemento MELON Extra",
            descripcion_corta_="Cemento MELON Extra",
            sku="800250",
        ),
        SkuTest(
            sku_id=8,
            descripcion_corta="Cadena Electrosoldada ACMA (12-17/15/20) Unidad",
            descripcion_corta_="Cadena Electrosoldada ACMA (12-17/15/20) Unidad",
            sku="Ce1520",
        ),
        SkuTest(
            sku_id=9,
            descripcion_corta="Cadena Electrosoldada ACMA (17-27/15-30) Unidad",
            descripcion_corta_="Cadena Electrosoldada ACMA (17-27/15-30) Unidad",
            sku="CA2030",
        ),
        SkuTest(
            sku_id=10,
            descripcion_corta="Pilar Electrosoldado ACMA (12-12/15-15) Unidad",
            descripcion_corta_="Pilar Electrosoldado ACMA (12-12/15-15) Unidad",
            sku="PE1515",
        ),
        SkuTest(
            sku_id=11,
            descripcion_corta="Pilar Electrosoldado ACMA (12-12/15-15) Unidad",
            descripcion_corta_="Pilar Electrosoldado ACMA (12-12/15-15) Unidad",
            sku="Pe340",
        ),
        SkuTest(
            sku_id=12,
            descripcion_corta="Hormigón Bombeable CBB H020(90)-20-12-32-28-B Unidad",
            descripcion_corta_="Hormigón Bombeable CBB H020(90)-20-12-32-28-B Unidad",
            sku="309842",
        ),
        SkuTest(
            sku_id=13,
            descripcion_corta="Perfil rectangular de acero TODO FIERRO RECT 30 X 70 X 3.0 Unidad",
            descripcion_corta_="Perfil rectangular de acero TODO FIERRO RECT 30 X 70 X 3.0 Unidad",
            sku="Ce 1520",
        ),
        SkuTest(
            sku_id=14,
            descripcion_corta="Perfil rectangular de acero TODO FIERRO RECT 100 X 50 X 4.0 Unidad",
            descripcion_corta_="Perfil rectangular de acero TODO FIERRO RECT 100 X 50 X 4.0 Unidad",
            sku="2090120	",
        ),
        SkuTest(
            sku_id=15,
            descripcion_corta="Perfil Angulo de Acero Laminado CINTAC Unidad",
            descripcion_corta_="Perfil Angulo de Acero Laminado CINTAC Unidad",
            sku="43000488",
        ),
        SkuTest(
            sku_id=16,
            descripcion_corta="Perfil Angulo de Acero Laminado TODO FIERRO ANG LAM 30 X 30 X 5.0 Unidad",
            descripcion_corta_="Perfil Angulo de Acero Laminado TODO FIERRO ANG LAM 30 X 30 X 5.0 Unidad",
            sku="36000388",
        ),
        SkuTest(
            sku_id=17,
            descripcion_corta="Producto que en su descr tiene Sku de otro producto ABCDEFG",
            descripcion_corta_="Producto que en su descr tiene Sku de otro producto ABCDEFG",
            sku="12345",
        ),
        SkuTest(
            sku_id=18,
            descripcion_corta="Producto cuyo Sku está en la descripción de otro producto",
            descripcion_corta_="Producto cuyo Sku está en la descripción de otro producto",
            sku="ABCDEFG",
        ),
    ]

    inserter = SkuInsertTest(connection=SYNC_CONN)

    inserter.bulk_request(documents)

    SkuTest._index.refresh()

def teardown_module(module):
    SYNC_CONN.indices.delete(index="test_index")

def sku_search_list_all_params():
    dataset = str(
        Path(__file__).with_name('test_crud_test_sku_search_list_all.tsv')
    )
    with open(dataset, newline='') as tsvfile:
        reader = csv.reader(tsvfile, delimiter='\t', quotechar='"')
        for ctr, row in enumerate(reader):
            if ctr == 0:
                continue
            elif ctr == 1:
                converters = [eval(col) for col in row]
                continue
            yield [c(col) for c,col in zip(converters, row)]


@pytest.mark.parametrize(
    "from_,size,rut_proveedor_,includes,excludes,include_meta",
    sku_search_list_all_params()
)
@pytest.mark.asyncio
async def test_sku_search_list_all(
    from_, size, rut_proveedor_, includes, excludes, include_meta
):
    searcher = SkuSearchTest(connection=ASYNC_CONN)

    results = await searcher.list_all(
        from_=from_,
        size=size,
        rut_proveedor_=rut_proveedor_,
        includes=includes,
        excludes=excludes,
        include_meta=include_meta,
    )

    assert results

    # from es zero-indexed y los datos parten con id 1
    assert results[0]['_source']['sku_id'] == from_+1

    # hay solo 5 datos con rut, asi que si size >5 debe encontrarlos todos
    assert len(results) == min((size, 5))

    # TODO: asserts for kwargs: includes, excludes, include_meta, etc
