# -*- coding: utf-8 -*-
""" Prueba sobre la funcionalidad del autocompletado """
import pytest

from . import SkuTest
from . import SkuSearchTest
from . import SkuInsertTest
from . import SYNC_CONN
from . import ASYNC_CONN

TEST_DATA_MATCH_EXACTO = [
    ("Arena melon aridos unidad", [("Arena MELON ARIDOS Unidad", "A10N")]),
    (
        "bmbehM2025",
        [
            (
                "Hormigón Preparado AISLANTES NACIONALES Bolsa 25 kg",
                "BMBEHM2025",
            )
        ],
    ),
    (
        "Cadena electrosoldada acma (17-27/15-30) Unidad",
        [("Cadena Electrosoldada ACMA (17-27/15-30) Unidad", "CA2030")],
    ),
    (
        "Cemento cBb especial Unidad",
        [("Cemento CBB Especial Unidad", "200032")],
    ),
    (
        "Grava Melon Aridos Unidad",
        [
            ("Grava MELON ARIDOS Seca Unidad", "G40N"),
            ("Grava MELON ARIDOS Normal Unidad", "203496"),
        ],
    ),
    (
        "Cemento",
        [
            ("Cemento CBB Especial Unidad", "200032"),
            ("Cemento MELON Extra", "800250"),
        ],
    ),
    ("Notebook", []),
    (
        "Producto que en su descr tiene Sku de otro producto ABCDEFG",
        [
            (
                "Producto que en su descr tiene Sku de otro producto ABCDEFG",
                "12345",
            )
        ],
    ),
]


TEST_DATA_MATCH_EXACTO_ORDENADO_PRIORIDAD_SKU = [
    (
        "Cemento 200032",
        [
            ("Cemento CBB Especial Unidad", "200032"),
            ("Cemento MELON Extra", "800250"),
        ],
    ),
    (
        "Hormigón Bombeable BMBEHM2025",
        [
            (
                "Hormigón Preparado AISLANTES NACIONALES Bolsa 25 kg",
                "BMBEHM2025",
            ),
            ("Hormigón Bombeable CBB H020(90)-20-12-32-28-B Unidad", "309842"),
        ],
    ),
    (
        "Grava MELON ARIDOS Seca 203496",
        [
            ("Grava MELON ARIDOS Normal Unidad", "203496"),
            ("Grava MELON ARIDOS Seca Unidad", "G40N"),
            ("Arena MELON ARIDOS Unidad", "A10N"),
            ("Cemento MELON Extra", "800250"),
        ],
    ),
]


def setup_module(module):

    if not SYNC_CONN.indices.exists(index="test_index"):
        SkuTest.init(using=SYNC_CONN)

    documents = [
        SkuTest(
            sku_id=1,
            descripcion_corta="Arena MELON ARIDOS Unidad",
            sku="A10N",
            descripcion_corta_="Arena MELON ARIDOS Unidad",
        ),
        SkuTest(
            sku_id=2,
            descripcion_corta="Arena CBB Semi Industrial Unidad",
            descripcion_corta_="Arena CBB Semi Industrial Unidad",
            sku="203421",
        ),
        SkuTest(
            sku_id=3,
            descripcion_corta="Grava MELON ARIDOS Normal Unidad",
            descripcion_corta_="Grava MELON ARIDOS Normal Unidad",
            sku="203496",
        ),
        SkuTest(
            sku_id=4,
            descripcion_corta="Grava MELON ARIDOS Seca Unidad",
            descripcion_corta_="Grava MELON ARIDOS Seca Unidad",
            sku="G40N",
        ),
        SkuTest(
            sku_id=5,
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

@pytest.mark.parametrize("input_text, expected", TEST_DATA_MATCH_EXACTO)
@pytest.mark.asyncio
async def test_exact_match(input_text, expected):
    """Prueba para ver match exacto, sin importar el orden """
    searcher = SkuSearchTest(connection=ASYNC_CONN)

    results = await searcher.search_product(input_text)

    short_descriptions = [
        (result["descripcion_corta"], result["sku"]) for result in results
    ]

    short_descriptions.sort()

    expected.sort()

    assert short_descriptions == expected


@pytest.mark.parametrize(
    "input_text, expected", TEST_DATA_MATCH_EXACTO_ORDENADO_PRIORIDAD_SKU
)
@pytest.mark.asyncio
async def test_exact_orderer_match(input_text, expected):
    searcher = SkuSearchTest(connection=ASYNC_CONN)

    results = await searcher.search_product(input_text)

    short_descriptions = [
        (result["descripcion_corta"], result["sku"]) for result in results
    ]

    assert short_descriptions == expected
