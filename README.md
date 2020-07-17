# Laholio


# Conexión a ElasticSearch
Para conectarse a ElasticSearch se deben configurar las variables de entorno `ELATICSEARCH_USER` y `ELASTICSEARCH_PASSWORD`. No es necesario configurar estas variables si la conexión es local, por ejemplo a través de Docker. 

Soporta dos tipos de conexiones. La primera, es la conexión clásica usada en la librería `elasticsearch-py`, la cual usa una clase de transporte que soporta métodos sincrónicos. La segunda, corresponde a una conexión usando una clase de transporte que soporta llamadas asincrónicas, construida en la librería `elasticsearch-async`

```python
 from laholio.connection import ElasticSearchConnection

es = ElasticSearchConnection() # Instancia con configuración por defecto
conn = es.connection # retorna la conexión a ES
```
La conexión `conn` es una instancia de la clase `Elasticsearch` de `elasticsearch-py`. 
Además:
  - El parámetro `transport_type` puede ser `sync`o `async`, el cual setea la tranport class como síncrona o asíncrona. Por defecto esta seteado en `sync`.
  - El parámetro `alias` en `ElasticSearchConnection` registra la conexión con dicho nombre en la librería `elasticsearch_dsl`.
  - Si se configura la variable `ELASTICSEARCH_SSL_CERT_PATH`, buscará el path y se usará conexión SSL.
  - `kwargs`adicionales serán pasados al método `create_connection` de `elasticsearch_dsl`.

## Iniciar los esquemas definidos en laholio
En laholio hay dos índices definidos, los cuales son `Sku` y `CatalogoUpload`. En el primero se encuentra la definición del catálogo y en el segundo se registra el status de los catálogos subidos por los proveedores (se reportan los errores de validación con respecto al catálogo definido en  `Sku`).

```python
 from laholio.schemas import Sku, CatalogoUpload, init_schema

init_schema(elasticsearch_connection, doc = Sku)
init_schema(elasticsearch_connection, doc = CatalogoUpload)

```

donde `elasticsearch_connection` es una conexión a elasticsearch **sincrónica**.

### Busqueda sobre el catálogo

La búsqueda esta pensada para ser realizada en una API con métodos asíncronos.

```python
from laholio.connection import ElasticSearchConnection as e
from laholio.crud import SkuSearch

async_connection e(transport_type = "async")
searcher = SkuSearch(connection = async_connection)

```
Por defecto `SkuSearch` apunta hacía el índice definido en `laholio.schemas.Sku`. 