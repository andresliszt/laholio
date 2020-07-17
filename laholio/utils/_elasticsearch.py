# -*- coding: utf-8 -*-
"""Utilidades varias para elasticsearch_dsl."""
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Type
from typing import Union

from elasticsearch_dsl import Document as _Document
from elasticsearch_dsl import Field
from elasticsearch_dsl.document import DocumentMeta
from elasticsearch_dsl.document import IndexMeta
from pydantic import BaseModel
from pydantic import Schema
from pydantic import create_model

from laholio.utils._fields import Float  # pylint: disable=no-name-in-module
from laholio.utils._fields import Integer  # pylint: disable=no-name-in-module
from laholio.utils._fields import Keyword  # pylint: disable=no-name-in-module
from laholio.utils._fields import Nested  # pylint: disable=no-name-in-module
from laholio.utils._fields import Object  # pylint: disable=no-name-in-module
from laholio.utils._fields import Text  # pylint: disable=no-name-in-module


class EnumText(Text):
    """Valida que el Texto pertenezca a un Enum."""

    # TODO: @sandoval: pq no es un keyword de Elastic?

    def __init__(self, *args, **kwargs):
        try:
            self._enum_class = kwargs.pop("enum_class")
            self._values = [e.value for e in self._enum_class]

        except KeyError:
            raise ValueError(
                "El constructor debe recibir un `Enum` en 'enum_class'"
            )
        super().__init__(*args, **kwargs)

    def clean(self, data):
        """Asegura que el texto pertenezca al `Enum` correspondiente."""
        data = super().clean(data)

        if (data is not None) and (data not in self._values):
            raise ValueError(
                "Valor invalido, posibles:{}".format(self._values)
            )
        return data

    @property
    def conversion(self):
        """`Callable`  para castear elasticsearch -> `Enum`."""
        return self._enum_class

    # TODO: ABSTRACT CLASSS PARA Fields propios


class Document(_Document):
    """Equipa los Documentos de elasticsearch con varias utilidades.

    utils: to_pydantic, extra_meta_field, y to_dict_with_custom_id.

    """

    TYPE_EQUIV_BASE = {Text: str, Keyword: str, Integer: int, Float: float}
    CUSTOM_FIELD_CLASS = {EnumText}

    @classmethod
    def __field_conversion(cls, field):
        if any(isinstance(field, custom) for custom in cls.CUSTOM_FIELD_CLASS):
            return field.conversion
        return cls.TYPE_EQUIV_BASE[type(field)]

    @classmethod
    def _build_conversion_updates(cls, name, field_class, required):
        casted = cls.__field_conversion(field_class)
        default = field_class._default  # pylint: disable=W0212
        description = field_class._description  # pylint: disable=W0212
        return {
            name: (
                casted if required else Optional[casted],
                Schema(... if required else default, description=description),
            )
        }

    @classmethod
    def __create_model(
        cls,
        name: str,
        fields: List[Tuple[str, Field, bool]],
        attributes: Optional[dict] = None,
    ) -> Type[BaseModel]:
        """Crea modelo de pydantic a partir de lista de campos de ES.

        Este método solo se debe usar cuando el esquema de ES no contiene
        campos del tipo Object o Nested.

        Args:
            equivalence_dict: Diccionario equivalencia entre el tipo de data
                que representa la clase :class:`elasticsearch_dsl.Field` y su
                equivalente tipo en python. Llaves

            name : Prefijo de nombre del modelo de pydantic.
                Nombre del modelo = name + "Pydantic".

            fields: Lista de tuplas de orden 3. Las tuplas contienen el nombre
                del campo, una instancia de  :class:`elasticsearch_dsl.Field`
            attributes : Atributos extra a incluir al modelo de pydantic.

        Ver Más:
            Buscar `create_model` en
                `https://pydantic-docs.helpmanual.io/usage/models/`

        """

        attributes = attributes or {}

        for _name, field_class, required in fields:

            updates = cls._build_conversion_updates(
                _name, field_class, required
            )
            attributes.update(updates)

        return create_model(name + "Pydantic", **attributes)

    @staticmethod
    def _get_fields(
        *,
        document_meta: Union[IndexMeta, DocumentMeta],
        excludes: Optional[List[str]] = None,
    ) -> List[Tuple[str, Field, bool]]:
        """Obtiene los campos del documento, y sus propiedades.

        Obtiene el nombre, la instancia de :class: `elasticsearch_dsl.Field`,
        y si el booleano de si el campo es requerido.

        Args:
            document_meta: Documento o documento a interior del que se sacarán
                los campos

            excludes: Lista de campos que se quieren excluir.

        """

        fields = []
        excludes = excludes or []
        for name, field, _ in document_meta._ObjectBase__list_fields():
            if name not in excludes:
                fields.append((name, field, bool(field._required)))

        return fields

    @classmethod
    def __to_pydantic(
        cls,
        name: str,
        excludes: Optional[List[str]],
        *,
        document_meta: Optional[Union[IndexMeta, DocumentMeta]] = None,
    ) -> Type[BaseModel]:
        """Transforma modelo de elasticsearch_dsl en pydantic."""

        document_meta = document_meta or cls

        excludes = excludes or None

        fields = cls._get_fields(
            document_meta=document_meta, excludes=excludes
        )

        if not fields:
            if isinstance(document_meta, DocumentMeta):
                # DocumentMeta corresponden a los inner docs; el riase solo
                # entra si el index inicial esta vacío
                # Por defecto estamos retornando key:value como string,
                # en los Object fields que estan seteados como dynamyc.
                # TODO: Generalizar a cualquier tipo de datatype! (?)
                return Dict[str, str]
            raise NotImplementedError
            # Aqui solo entra en un indice sin fields! ó excludes abarca todos
            # los fields
            # TODO: Custom Errror

        not_object_fields, object_model = [], {}
        for _name, field, required in fields:
            if isinstance(field, Object):
                inner_document_meta = field._doc_class
                model = (
                    List[
                        cls.__to_pydantic(
                            _name,
                            excludes=None,
                            document_meta=inner_document_meta,
                        )
                    ]
                    if isinstance(field, Nested)
                    else cls.__to_pydantic(
                        _name, excludes=None, document_meta=inner_document_meta
                    )
                )

                object_model.update(
                    {_name: (model if required else Optional[model], ...)}
                )

            else:
                not_object_fields.append((_name, field, required))
        return (
            cls.__create_model(name, not_object_fields, object_model)
            if object_model
            else cls.__create_model(name, fields)
        )

    @classmethod
    def to_pydantic(cls, name: str, excludes: Optional[List[str]] = None):
        """Genera un ``pydantic.BaseModel`` de acuerdo a la clase."""
        return cls.__to_pydantic(name, excludes=excludes)

    @classmethod
    def extra_meta_field(cls, **meta_kw):
        """Usar para setear metafields extras!.

        Solo en subclases!.

        """
        cls._doc_type.mapping._meta.update(meta_kw)

    def to_dict_with_custom_id(self, **kwargs):
        """Este método debe definir de qué manera se definen ids."""
        raise NotImplementedError("Este método debe ser sobrescrito")


def decora_synonym(func):
    """Habilita un Field de Elasticsearch con kwarg sinonimo."""

    def wrapper(self, *args, **kwargs):
        try:
            self.synonym = kwargs.pop("synomym")
        except KeyError:
            pass
        func(self, *args, **kwargs)

    return wrapper


def add_synonym(_field):
    """Agrega sinommo a un elasticsearch.Field como kwarg."""

    if not issubclass(_field, Field):
        raise TypeError

    field_ = type(
        "field", (_field,), {"__init__": decora_synonym(_field.__init__)}
    )

    return field_
