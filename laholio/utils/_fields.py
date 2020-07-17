"""Utilidad para agregar atributos a :class:`elasticsearch_dsl.Field`"""

import elasticsearch_dsl.field as field_module

Field = field_module.Field


def decorardor(func):
    """Habilita un documento de Elasticsearch con campos adicionales."""

    def wrapper(self, *args, **kwargs):
        description = kwargs.pop("description", "")
        default = kwargs.pop("default", None)
        func(self, *args, **kwargs)
        self._description = description  # pylint: disable=W0212
        self._default = default  # pylint: disable=W0212

    return wrapper


for name, elem in field_module.__dict__.items():
    try:
        if issubclass(elem, Field) and name not in ("Field", "CustomField"):
            cp = type(name, (elem,), {"__init__": decorardor(elem.__init__)})
            globals().update({name: cp})

    except TypeError:
        pass
