# -*- coding: utf-8 -*-
import pytest


def test_import():
    import laholio

    meta = laholio.__meta__
    assert meta


@pytest.mark.parametrize(
    "name",
    [
        ("name"),
        ("version"),
        ("description"),
        ("author"),
        ("license"),
        ("home-page"),
        ("author-email"),
        ("summary"),
    ],
)
def test_attr(name):
    import laholio

    metadata = laholio.__meta__
    assert metadata[name]
