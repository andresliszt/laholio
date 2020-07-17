"""Operaciones CRUD."""
# -*- coding: utf-8 -*-
from typing import Iterable
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from elasticsearch_dsl import Q
from elasticsearch_dsl import Search
from elasticsearch_dsl.response import Response

from laholio import logger
from laholio.connection import AsyncTransport
from laholio.exceptions import IndexNotExists
from laholio.exceptions import NotAsyncEsConnection
from laholio.exceptions import NotUsingEsConnection
from laholio.exceptions import NotUsingIndex
from laholio.schemas import CatalogoUpload
from laholio.schemas import Sku
from laholio.utils._elasticsearch import Document
from laholio.utils.async_dsl import AsyncSearch
from laholio.utils.async_dsl import AsyncTasks


class Base:  # pylint: disable=R0903

    """Clase base para operaciones crud.

    Agregar aca funcionalidades comunes.

    """

    def __init__(self, connection: Elasticsearch, index_name: str):

        if not connection.indices.exists(index_name):
            raise IndexNotExists(index=index_name)

        self.connection = connection
        self.index_name = index_name


class BaseAsyncSearch(Base):
    """Clase base para operaciones de búsquedas asincrónicas."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not isinstance(self.connection.transport, AsyncTransport):
            raise NotAsyncEsConnection(connection=self.connection)

    @property
    def search_base(self):
        """Búsqueda con la configuración básica."""
        search = AsyncSearch(using=self.connection, index=self.index_name)
        return search

    @staticmethod
    def construct_multi_field_search(  # pylint: disable=too-many-arguments
        search: AsyncSearch,
        text: str,
        operator: str,
        fields: List[str],
        size: int = 5,
        includes: Optional[List[str]] = None,
        excludes: Optional[List[str]] = None,
    ) -> AsyncSearch:
        """Construye búsqueda por texto en multiples campos.

        Args:

            search: Búsqueda inicial.
            text: Texto de busquéda.
            operator: Condicional sobre los tokens del texto. Si el
                operator es `and`, entonces para que haya match, todos los
                tokens deben ser encontrados en el índice inverso. Si el
                operator es `or`, entonces para que haya match, al menos un
                token debe ser encontrado en el índice inverso.
                Ver:
                    https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-match-query.html
            size: Tamaño de la busqueda. Valor por defecto 5.
            includes: Control selectivo del campo _source.
                    Retorna solo los campos que se especifican.

            excludes: Control selectivo del campo _source.
                    Excluye los campos que se especifican.

            fields: Nombre de los fields de :class:~`laholio.schemas.Sku`
                en donde se quiere buscar

        Returns:
            search: Search

        """
        if search._using is None:
            raise NotUsingEsConnection

        if search._index is None:
            raise NotUsingIndex

        if includes:
            search = search.source(includes=includes)

        if excludes:
            search = search.source(excludes=excludes)

        search = search.query(
            Q("multi_match", query=text, operator=operator, fields=fields)
        )

        search = search.params(size=size)

        logger.info("Query", query=search.to_dict())

        return search

    async def suggest(
        self, text: str, field_name, suggestion_type, suggestion_name: str
    ) -> List[str]:
        """Corrección/sugerencia de un texto
        Args:
            field_name: Nombre del campo de referencia para sugerir.
            suggestion_type: Tipo de sugerencia de ES, `phrase` o `term`.
            suggestion_name : Identificador de la sugerencia.
            text: Texto de entrada.
        Returns:
           Lista con las opciones de sugerencia de texto. Retorna una lista
                vacía si es que no hay sugerencias.
        """
        search = self.search_base

        if suggestion_type not in ("phrase", "term"):
            raise ValueError(
                "Parámetro `suggestion_type` debe ser `term` o `phrase`"
            )

        if suggestion_type == "phrase":
            search = search.suggest(
                suggestion_name,
                text,
                phrase={"field": field_name, "max_errors": 3},
            )

        elif suggestion_type == "term":
            search = search.suggest(
                suggestion_name,
                text,
                term={"field": field_name, "max_errors": 3},
            )

        response = await search.execute()

        if not hasattr(response, "suggest"):
            raise NotImplementedError  # TODO: Cuando el índice no tiene docs
            # entra a este error, why? que otro caso?

        suggestions = response.suggest

        # Como hicimos una sola sugerencia, la información estará
        # en el único elemeno de la lista
        suggestions = suggestions[suggestion_name][0]

        return [suggest.text for suggest in suggestions.options]

    @staticmethod
    def _hit_dsl_conversor(hit, include_meta: bool):
        return hit.to_dict() if include_meta else hit.to_dict()["_source"]

    @staticmethod
    def _hit_conversor(hit: dict, include_meta: bool):
        return hit if include_meta else hit["_source"]

    def serialize(
        self, response: Union[Response, dict], include_meta: bool
    ) -> List[dict]:
        """Serializa los resultados de una busqueda.

        Args:
            response: Resultados de la búsqueda sin procesar. Esta response
                puede ser la clase de respuesta de la librería
                `elasticsearch_dsl`, ó el diccionario de respuesta que entrega
                la librería de más bajo nivel `elasticsearch-py`
            include_meta: Si es `True`, agrega en el serializado los campos
                de `_id`, `_score`, `_index`.

        """

        conversor = getattr(
            self,
            "_hit_dsl_conversor"
            if isinstance(response, Response)
            else "_hit_conversor",
        )

        hits = response["hits"]["hits"]  # Ambas respuestas dsl y es-py

        serialized = [conversor(hit, include_meta) for hit in hits]

        return serialized

    async def init_scroll(
        self,
        search: AsyncSearch,
        pag_size: int,
        include_meta: bool = False,
        scroll: str = "1m",
    ) -> Tuple[List[dict], int]:
        """Inicialización de la scroll API de elasitcsearch.

        Args:
            search : Búsqueda inicial para la scroll API.
            pag_size : Tamaño de la paginación.
            include_meta : Incluir o no metadatos asociados a la búsqueda.
            scroll : Tiempo en que se dejará abierto el search context.

        Returns:
            Lista serializada de matchs,
              y el scroll_id para continuar con la paginación.

        """

        search = search.params(size=pag_size, scroll=scroll)

        response = await search.execute()

        serialized = self.serialize(response, include_meta=include_meta)

        scroll_id = response["_scroll_id"]

        return serialized, scroll_id

    async def next_page(
        self, scroll_id: int, include_meta: bool = False, scroll: str = "1m"
    ):
        """Consulta al scroll API de elasticsearch usando scroll id."""

        connection = self.connection
        response = await connection.scroll(
            body={
                "scroll_id": scroll_id,  # pylint: disable=used-before-assignment
                "scroll": scroll,
            }
        )
        scroll_id = response["_scroll_id"]

        serialized = self.serialize(response, include_meta)

        return serialized, scroll_id


class SkuSearch(BaseAsyncSearch):
    """Operaciones CRUD para el :class:`laholio.schemas.Sku`."""

    def __init__(self, connection: Elasticsearch):
        super().__init__(connection, Sku.Index.name)
        self.last_search: Optional[AsyncSearch] = None

    @staticmethod
    def _filter_brand(
        search: AsyncSearch, rut_proveedor_: Union[int, List[int]]
    ) -> Search:
        """Agrega un filter context sobre el field `rut_proveedor_`

        :class:~`laholio.schemas.Sku`

        Args:
            search: Búsqueda a la cual agregar el filter context
            rut_proveedor_ : rut o lista de ruts para realizar filtro por
            proveedores. Se considera este argumento como el rut del proveedor
            sin el digito verificador, tratado como entero.
                e.g: '96885880-7' -> 96885880.
        Return
            Búsqueda con el filtro por rut(s).

        """
        return search.filter(
            "term" if isinstance(rut_proveedor_, int) else "terms",
            rut_proveedor_=rut_proveedor_,
        )
        # Importa la diferencia entre term y terms!

    async def search_product_by_sku(
        self,
        sku: str,
        rut_proveedor_: Optional[Union[int, List[int]]] = None,
        include_meta: bool = False,
    ) -> List[dict]:
        """Búsqueda directa por código sku."""
        search = self.search_base

        if rut_proveedor_:
            search = self._filter_brand(search, rut_proveedor_)

        search = search.query("match", sku=sku)  # pylint: disable=no-member

        response = await search.execute()

        serialized = self.serialize(
            response=response, include_meta=include_meta
        )

        return serialized

    async def _search_product(  # pylint: disable=too-many-arguments
        self,
        text: str,
        search_operator: str,
        search_size: int = 5,
        rut_proveedor_: Optional[Union[int, List[int]]] = None,
        includes: Optional[List[str]] = None,
        excludes: Optional[List[str]] = None,
        include_meta=False,
    ) -> List[dict]:
        """Busca un Sku dado un texto.

        Busca en los campos `descripcion corta` y `sku` de
        :class:~`laholio.schemas.Sku` por texto, dándole mayor peso
        al campo `sku`. Esto significa si en la búsqueda viaja el código
        sku del proveedor, entonces debería mostrarse como en primera
        opción dicho sku.

        Args:
            text : Texto de búsqueda
            rut_proveedor_: rut o lista de
            ruts para realizar filtro por proveedores. Se considera este
            argumento como el rut del proveedor sin el digito verificador,
            tratado como entero. e.g: '96885880-7' -> 96885880.
            include_meta : Si es True, muestra los meta fields
            de los matches.

            Los demás argumentos corresponden a los argumentos de
                :func: `~laholio.crud.SkuSearch.construct_multi_field_search`

        Returns:
            Lista serializada de productos encontrados. Si no hay
            matches retorna una lista vacía

        """

        excludes = excludes or ["descripcion_corta_"]

        search_base = self.search_base

        if rut_proveedor_ is not None:
            search_base = self._filter_brand(search_base, rut_proveedor_)

        search = self.construct_multi_field_search(
            search_base,
            text,
            search_operator,
            fields=["sku^10", "descripcion_corta"],
            size=search_size + 1,
            includes=includes,
            excludes=excludes,
        )

        response = await search.execute()

        serialized = self.serialize(response, include_meta=include_meta)

        if len(serialized) > search_size:
            self.last_search = search
            serialized = serialized[:search_size]
        else:
            self.last_search = None

        return serialized

    async def search_product(self, text, **kwargs):

        """Busqueda de sku dado un texto.

        Se hace una búsqueda con la siguiente lógica. De manera asincrónica
        se consulta a elasticsearch usando la función
        :func:`~laholio.crud.SkuSearch._search_product` con operadores
        de nexo entre tokens `and` y `or`, y además se
        realiza sugerencia con :func:`~laholio.crud.SkuSearch.suggest_product`.

        Las tareas están siendo controladas por
        :class: `~laholio.utils.async_dsl.AsyncTasks`, en la cual las tareas
        se ejecutan de manera asincrona, pero tienen prioridades, es decir,
        se retorna el resultado de la tarea exitosa ordenada por prioridad, y
        las restantes son canceladas. El orden de este método es buscar con
        prioridad 1 usando `and`, prioridad 2 usando `or` y prioridad 3 la
        sugerencia.

        """

        result = await AsyncTasks.quickexit(
            lambda r: bool(r),  # pylint: disable=unnecessary-lambda
            self._search_product(text, search_operator="and", **kwargs),
            self._search_product(text, search_operator="or", **kwargs),
            self.suggest_product(text, **kwargs),
        )

        return result

    async def suggest_product(self, text, **kwargs):
        """Sugerencia de sku, dado un texto.

        Este método hace dos consultas. Primero, dado el texto, intenta
        corregirlo (si necesita ser corregido), si el texto fue corregido,
        realiza la query usando :meth:`laholio.crud.SkuSearch._search_product`

        Kwargs:
            corresponden a los kwargs
                :meth:~`laholio.crud.BaseAsyncSearch.suggest`

        """

        suggested_text = await self.suggest(
            text=text,
            field_name="descripcion_corta_",
            suggestion_type="phrase",
            suggestion_name="sku_suggest",
        )

        if suggested_text:
            return await self._search_product(
                suggested_text[0], search_operator="or", **kwargs
            )
        return list()

    async def _compaginated_search(  # pylint: disable=too-many-arguments
        self,
        search: AsyncSearch,
        pag_size: int,
        scroll_timeout: str = "1m",
        scroll_kwargs: dict = None,
        include_meta: bool = False,
    ):
        """Búsqueda compaginada usando la scroll API de ES.

        Se encuentran todos los matches dada una query. En esta búsqueda
        no importa el orden (meta field _score es ignorado). Ver más:
            https://www.elastic.co/guide/en/elasticsearch/reference/current/search-request-body.html#request-body-search-scroll

        Args:
            search: Búsqueda será ejecutada en la
                        scroll API.
            pag_size : Número de resultados por pagina
            scroll_timeout : Tiempo en que esta abierta
                        el search context . Default "1m".
            scroll_kwargs : Argumento scroll_kwargs
                        de :func:`ElasticSearch.scroll`.
            include_meta : Si es `True`, metadatos incluidos en los resultados.

        """

        connection = self.connection
        search = search.params(size=pag_size, scroll=scroll_timeout)
        scroll_kwargs = scroll_kwargs or {}
        is_first = True
        scroll_id: str
        try:
            while True:
                if is_first:
                    response = await search.execute()
                    is_first = False
                else:
                    response = await connection.scroll(
                        body={
                            "scroll_id": scroll_id,  # pylint: disable=used-before-assignment
                            "scroll": scroll_timeout,
                        },
                        **scroll_kwargs,
                    )
                scroll_id = response["_scroll_id"]
                serialized = self.serialize(response, include_meta)

                if not serialized:
                    break
                yield serialized

        finally:
            await connection.clear_scroll(
                body={"scroll_id": [scroll_id]}, ignore=(404,)
            )

    async def see_more(self, pag_size: int = 10, **kwargs):
        """Búsqueda compaginada usando la última búsqueda registrada."""
        # TODO: Levantar error para timeout -> más espefico e.g ScrollTimeOutEr
        if not self.last_search:
            raise ValueError("No hay más resultados que mostrar")

        async for results in self._compaginated_search(
            self.last_search, pag_size, **kwargs
        ):
            yield results

    async def list_all(
        self,
        *,
        from_: int,
        size: int,
        rut_proveedor_: Union[int, List[int]],
        includes: Optional[List[str]] = None,
        excludes: Optional[List[str]] = None,
        include_meta=False,
    ):

        """Lista todos los sku."""

        excludes = excludes or ["descripcion_corta_"]
        search_base = self.search_base

        if search_base._using is None:
            raise NotUsingEsConnection
        if search_base._index is None:
            raise NotUsingIndex

        search = self._filter_brand(search_base, rut_proveedor_)
        search = search.source(includes=includes, excludes=excludes)

        search = search.query(Q("match_all"))[from_ : size + 1]  # noqa: E203

        logger.info("Query", query=search.to_dict())

        response = await search.execute()
        serialized = self.serialize(response, include_meta=include_meta)

        if len(serialized) > size:
            self.last_search = search
            serialized = serialized[:size]
        else:
            self.last_search = None

        return serialized


class CatalogoUploadSearch(BaseAsyncSearch):
    """Operaciones CRUD para el :class:`laholio.schemas.CatalogoUpload`."""

    def __init__(self, connection: Elasticsearch):
        super().__init__(connection, CatalogoUpload.Index.name)

    async def search_by_field(
        self, field_name: str, field_value: str, include_meta=False
    ):
        """Búsqueda simple por rut del proveedor."""

        if field_name not in ("file_hash", "client_id", "rut_proveedor"):
            raise ValueError(
                "`field_name` es `file_hash`, `client_id` o `rut_proveedor`"
            )

        search = self.search_base
        search = search.query("match", **{field_name: field_value})

        response = await search.execute()

        serialized = self.serialize(
            response=response, include_meta=include_meta
        )

        return serialized


class BulkInsertUpdateDelete(Base):
    """Clase para insertador documentos en elasticSearch."""

    @staticmethod
    def prepare_bulk_dsl(
        documents: Iterable[Document], op_type: str, with_ids: bool
    ):
        """Prepara los documentos a ser insertados usando la bulk API.

        Los documentos son instancias de clases que heredan
        de `laholio.utils._elasticsearch.Document`.

        Si `with_ids` es True, se debe tener el método
        `to_dict_with_custom_id` definido, en el cual se prepara el
        documento para ser insertado y además el meta `_id` es
        construido de acuerdo alguna regla establecida.

        Si `with_ids` es False, entonces el `_id` sera construido por el
        cliente de elasticsearch.

        documents: Iterable/Generador de documentos con el formato
        descrito anteriormente.

        op_type: Pueder ser `index`, `update` o `delete`, os cuales
            indexan, actualizan o borran respectívamente los documentos

        with_ids: Booleano que indica si los documentos vienen con `_id`
        (True) o no (False).

        """
        if op_type not in ("index", "update", "delete"):
            raise ValueError(
                "`op_type` pueder ser `index`, `update` o `delete`"
            )

        conversor = (
            lambda document: document.to_dict_with_custom_id(include_meta=True)
            if with_ids
            else lambda document: document.to_dict(include_meta=True)
        )

        make_body = (
            lambda document: document.update(doc=document.pop("_source"))
            if op_type == "update"
            else None
        )
        for document in documents:
            document = conversor(document)
            document["_op_type"] = op_type
            make_body(document)
            yield document

    def prepare_bulk_raw(
        self, documents: Iterable[dict], op_type: str, with_ids: bool
    ):
        """Prepara los documentos a ser insertados usando la bulk API.

        Los documentos son diccionarios, en los siguientes formatos:

            Si `with_ids is True`:
                Se requiere el meta `_id` y el campo `_source` de elasticsearch

                document = {"_id": AlgunValor, "_source": source}

            En otro caso:

                El documento solo corresponde al diccionario source

                document = source

        Args:
            documents: Iterable/Generador de documentos con el formato descrito
                anteriormente.

            op_type: Pueder ser `index`, `update` o `delete`. Los cuales
                indexan, actualizan o borran respectívamente los documentos

            with_ids: Booleano que indica si los documentos vienen con `_id`
            (True) o no (False).

        """
        if op_type not in ("index", "update", "delete"):
            raise ValueError(
                " `op_type` pueder ser `index`, `update` o `delete`"
            )

        source_key = "doc" if op_type == "update" else "_source"

        def body(document):
            return {
                "_index": self.index_name,
                source_key: document["_source"],
                "_optype": op_type,
                "_type": "doc",
            }

        def body_id(document):
            return {**body(document), "_id": document["_id"]}

        make_body = body_id if with_ids else body

        for document in documents:
            document = make_body(document)
            yield document

    def bulk_request(
        self,
        documents: Union[Iterable[Document], Iterable[dict]],
        document_type: str = "dsl",
        op_type: str = "index",
        with_ids: bool = True,
        **kwargs,
    ):
        """Inserta un iterable/generator de documentos en su Index.

        Args:
            documents: Documentos a insertar
            document_type: `dsl` sin los documentos son instancias de
                `Document` o `raw` si son diccionarios puros.

        """
        logger.info("Enviando bulk request en el iterable/generator")
        if document_type not in ("raw", "dsl"):
            raise ValueError("`document_type` puede ser `raw` o `dsl`")

        if document_type == "dsl":
            objects = self.prepare_bulk_dsl(
                documents, op_type=op_type, with_ids=with_ids
            )

        elif document_type == "raw":
            objects = self.prepare_bulk_raw(
                documents, op_type=op_type, with_ids=with_ids
            )

        _kwargs = dict(
            client=self.connection,
            actions=objects,
            raise_on_exception=False,
            raise_on_error=False,
            stats_only=False,
        )

        _kwargs.update(**kwargs)

        res_succ, res_err = bulk(**_kwargs)

        logger.info(
            "Enviada la bulk request.",
            tipo=op_type,
            total_exitosos=res_succ,
            total_fallados=res_err,
        )

        for res in res_err:
            logger.warn(
                "Error en bulk request",
                **{
                    "LAHOLIO.EVENT": "BULK_ERROR",
                    "LAHOLIO.EXCEPTION": str(res),
                },
            )
