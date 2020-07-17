# -*- coding: utf-8 -*-
"""Clases del `elasticsearch_dsl` soportando métodos async."""
import asyncio

from elasticsearch_dsl import Search
from elasticsearch_dsl.connections import connections


class AsyncTasks:
    """Ejecuta tareas asincrónicas con método de retorno selectivo."""

    @staticmethod
    def schedule(*aws):
        """Inicia la ejecución asíncrona de las tareas."""
        return [asyncio.ensure_future(task) for task in aws]

    @classmethod
    async def quickexit(cls, validator, *aws):
        """Ejecuta y verifica de manera secuencial una serie de tareas.

        Si la tarea en verificación se ejecuta correctamente, el
        programa termina. De lo contrario, el programa revisa la
        próxima tarea, y así sucesivamente.

        La verificación viene dada por ``validator``.

        """

        tasks = cls.schedule(*aws)
        for task in tasks:
            result = await task
            if validator(result):
                break
        for task_ in tasks:
            task_.cancel()
        return result


class AsyncSearch(Search):
    """Implementa `execute`, `count` y `scan` de manera asíncrona."""

    async def execute(self, ignore_cache=False):
        """Ejecuta de manera asincrónica la busqueda."""
        if ignore_cache or not hasattr(self, "_response"):
            es = connections.get_connection(self._using)

            response = await es.search(
                index=self._index, body=self.to_dict(), **self._params
            )

            self._response = self._response_class(self, response)
        return self._response

    async def count(self):
        """Retorna el número de matches de manera asincrónica."""
        if hasattr(self, "_response"):
            return self._response.hits.total

        es = connections.get_connection(self._using)

        d = self.to_dict(count=True)
        # TODO: failed shards detection
        count = await es.count(index=self._index, body=d, **self._params)

        return count["count"]

    def scan(self):
        # TODO : Este método usa el scan de elasticsearch-py, la conversión
        # asincrona debe ser estudiada.
        raise NotImplementedError("Este método debe ser convertido a async")
