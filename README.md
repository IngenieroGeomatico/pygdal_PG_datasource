# pygdal_PG_datasource

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![GDAL](https://img.shields.io/badge/GDAL-3.0%2B-green)
![License](https://img.shields.io/badge/license-MIT-yellow)
![Status](https://img.shields.io/badge/status-alpha-orange)

**Acceso unificado a datos geoespaciales vectoriales y ráster vía GDAL/OGR, con conexión a PostgreSQL/PostGIS.**

`pygdal_PG_datasource` es una librería Python que abstrae el acceso a fuentes de datos geográficos mediante **GDAL/OGR** y la conexión a bases de datos **PostgreSQL/PostGIS** mediante **psycopg2**. Está diseñada para servir como capa de datos en proyectos que necesiten leer, transformar y exportar información geoespacial desde múltiples orígenes (archivos locales, WFS, WMS, MVT, WKT, GeoJSON embebido, PostGIS, etc.).

Además del acceso geoespacial clásico, la librería incorpora **conectores IoT** (Sonoff/eWeLink y Tuya Smart Life) capaces de descubrir dispositivos en la red local, leer su estado y exponerlos como capas geográficas (GeoJSON / OGR / SQLite).

> Este repositorio es un submódulo de [pygeoapi_complementos](https://github.com/IngenieroGeomatico/pygeoapi_complementos), que a su vez es un submódulo de [pygeoapi_plus](https://github.com/IngenieroGeomatico/pygeoapi_plus). Su propósito es proporcionar los bloques fundamentales de acceso a datos para una futura integración con **pygeoapi**.

---

## Estructura del repositorio

```
pygdal_PG_datasource/
├── conex/
│   ├── PG_conex.py                 # Conexión y consultas a PostgreSQL (psycopg2)
│   ├── Vector_conex.py             # Lectura, consulta y exportación vectorial (OGR)
│   ├── Raster_conex.py             # Lectura y exportación ráster (GDAL)
│   ├── sonoff_conex.py             # Conector IoT Sonoff/eWeLink → GeoJSON/OGR/SQLite
│   ├── tuyaSmartLife_conex.py      # Conector IoT Tuya Smart Life + exportación GeoJSON/OGR
│   ├── __init__.py                 # Convierte el directorio en paquete Python
│   ├── lib_sonoff/
│   │   ├── peticiones_sonoff.py    # Descubrimiento mDNS (zeroconf) de dispositivos
│   │   └── cripto_sonoff.py        # Cifrado/descifrado AES-CBC del estado (eWeLink)
│   └── lib_tuyaSmartLife/
│       └── peticiones_TuyaSmartLife.py  # Descubrimiento local (tinytuya)
├── procesos/
│   ├── __init__.py
│   └── vector/
│       ├── __init__.py
│       ├── geoprocesos.py          # Geoprocesos OGR (buffers)
│       └── tematicos.py            # Cálculos temáticos OGR (áreas)
├── tests/                          # Suite de tests (pytest)
│   ├── conftest.py                 # Añade la raíz del repo al sys.path
│   ├── test_geojson_query.py       # Unit: consultas GeoJSON + seguridad filtro
│   ├── test_pg_conex.py            # Unit: ConexPG (psycopg2 mockeado)
│   ├── test_tuya_peticiones.py     # Unit: descubrimiento Tuya (tinytuya mockeado)
│   ├── test_tuya_datos.py          # Unit: transformación datos Tuya
│   ├── test_cripto_sonoff.py       # Unit: cifrado AES (requiere pycryptodome)
│   ├── test_sonoff_sqlite.py       # Unit: Sonoff desde SQLite
│   ├── test_vector_conex.py        # Unit: FuenteDatosVector (requiere GDAL)
│   ├── test_procesos_vector.py     # Unit: buffers/áreas (requiere GDAL)
│   └── integration/                # Tests de integración (recursos reales)
│       ├── helpers.py              # Utilidades de skip (red/GDAL)
│       ├── conftest.py             # Fixtures de credenciales por env vars
│       ├── test_vector_integracion.py
│       ├── test_raster_integracion.py
│       ├── test_pg_integracion.py
│       ├── test_sonoff_integracion.py
│       └── test_tuya_integracion.py
├── pyproject.toml                  # Configuración del paquete Python
├── pytest.ini                      # Configuración de pytest
├── tmp/                            # Directorio temporal para exportaciones
└── README.md
```

> **Nota:** el código de la librería vive en `conex/` (no en un paquete `lib/`). Los ejemplos de importación de este README usan `conex.*`. El directorio `conex/` ya contiene `__init__.py` y puede importarse directamente.

---

## Requisitos

- **Python** 3.8 o superior
- **GDAL/OGR** 3.0 o superior (`python3-gdal` o `gdal` vía pip)
- **psycopg2** (`psycopg2` o `psycopg2-binary`) — solo necesario para el módulo `PG_conex`

### Instalación de dependencias

Dependencias base (vector/ráster + PostgreSQL):

```bash
# Con pip
pip install gdal psycopg2-binary

# En Debian/Ubuntu
sudo apt install python3-gdal python3-psycopg2

# En entornos Conda
conda install -c conda-forge gdal psycopg2
```

Dependencias adicionales solo para los conectores IoT:

```bash
# Sonoff/eWeLink
pip install requests zeroconf pycryptodome

# Tuya Smart Life
pip install tinytuya
```

---

## Instalación

```bash
git clone https://github.com/IngenieroGeomatico/pygdal_PG_datasource.git
cd pygdal_PG_datasource
pip install .
```

Para incluir dependencias opcionales (conectores IoT):

```bash
pip install .[sonoff]    # Sonoff/eWeLink
pip install .[tuya]      # Tuya Smart Life
pip install .[all]       # Todos los conectores IoT
```

El directorio `conex/` es un paquete Python (contiene `__init__.py`). Puedes importar los módulos directamente:

```python
from conex.PG_conex import ConexPG
from conex.Vector_conex import FuenteDatosVector
from conex.Raster_conex import FuenteDatosRaster
```

---

## Módulos

### 1. PG_conex — Conexión PostgreSQL

**Archivo:** `conex/PG_conex.py`  
**Clase:** `ConexPG`

Gestiona la conexión a una base de datos PostgreSQL y la ejecución de consultas SQL mediante **psycopg2**.

#### Configuración

La conexión se parametriza mediante un diccionario con estas claves:

| Clave    | Descripción           |
|----------|-----------------------|
| `IP`     | Host o IP             |
| `port`   | Puerto (por defecto 5432) |
| `user`   | Usuario               |
| `pass`   | Contraseña            |
| `db`     | Nombre de la base de datos |

Se puede pasar directamente al constructor o cargarla desde un archivo JSON.

#### Métodos

| Método                               | Descripción                                    |
|--------------------------------------|------------------------------------------------|
| `__init__(dataJSONcon=None)`         | Constructor. Si no se pasa JSON, intenta leer `./conex/PGconex.json`. Si el archivo no existe, lo crea con valores vacíos y lanza una excepción. |
| `conex2PG(check=False)`              | Establece conexión a PostgreSQL. Si `check=True`, abre y cierra la conexión (modo verificación) y devuelve un mensaje de confirmación. Si `check=False`, retorna el objeto `connection` abierto. |
| `queryPG(query)`                     | Abre una conexión, ejecuta la consulta SQL, hace `fetchall()`, `commit()` y cierra la conexión (incluso ante errores). Retorna los resultados. |

---

### 2. Vector_conex — Datos vectoriales con OGR

**Archivo:** `conex/Vector_conex.py`  
**Clase:** `FuenteDatosVector`

Clase para leer, consultar y exportar datos vectoriales usando **OGR** (GDAL). Soporta múltiples tipos de entrada:

| Tipo de entrada          | Ejemplo                                           |
|--------------------------|---------------------------------------------------|
| Archivo local            | `"ruta/datos.geojson"`                            |
| URL (WFS, GeoJSON, etc.) | `"http://servidor/datos.geojson"`                 |
| WKT                      | `"POINT (1120351 741921)"`                        |
| GeoJSON embebido (string)| `'{"type":"FeatureCollection","features":[...]}'` |
| MVT (Mapbox Vector Tiles)| `"MVT:https://servidor/{z}/{x}/{y}"`              |
| ZIP                      | `"http://servidor/datos.zip"`                     |

#### Métodos principales

| Método                                       | Descripción                                                                 |
|----------------------------------------------|-----------------------------------------------------------------------------|
| `probar_gdal_ogr()` *(static)*               | Diagnóstico: muestra la versión de GDAL y lista los drivers vectoriales y ráster disponibles. |
| `__init__(dato)`                             | Almacena la ruta/URL/WKT de la fuente de datos.                            |
| `leer(capa=None, EPSG_Entrada=None, datasetCompleto=False)` | Abre la fuente y la copia a un datasource en memoria (driver MEMORY). Si `datasetCompleto=True` (y `capa=None`), carga todas las capas. Para URLs HTTP antepone `/vsicurl/`; para ZIP, `/vsizip/`. WKT se convierte en un layer en memoria (requiere `EPSG_Entrada`). |
| `exportar(capa=None, EPSG_Salida=None, outputFormat='application/json', ID=None)` | Con `outputFormat='application/json'`/`'json'` devuelve un **dict GeoJSON** reproyectado a EPSG:4326 (opcionalmente asignando `id` a partir del campo `ID`). Con cualquier otro formato OGR (Shapefile, GPKG, etc.) escribe a `./tmp/`, reproyecta a `EPSG_Salida` y devuelve el archivo como **bytes**; si hay varias capas y el driver no soporta multicapa, genera un ZIP. |
| `obtener_atributos(capa=None)`               | Retorna un diccionario con los nombres de campo y sus tipos para una capa o todas las capas. |
| `obtener_capas()`                            | Lista los nombres de todas las capas del datasource.                       |
| `obtener_nombreCapa(capa=None)` / `obtener_indice_capa(nombre)` | Resuelven nombre/índice de capa.                          |

#### Consulta y geoprocesamiento sobre el datasource en memoria

| Método                                       | Descripción                                                                 |
|----------------------------------------------|-----------------------------------------------------------------------------|
| `ejecutar_sql(sql, capa, dialect='OGRSQL')`  | Ejecuta SQL OGR (o `SQLITE`) y guarda el resultado como nueva capa.         |
| `MRE_datos(capaEntrada, capaSalida, MRE, EPSG_MRE=4326)` | Filtro espacial por bounding box; guarda la capa filtrada.      |
| `reproyectar_datasource(EPSG_salida)`        | Reproyecta todas las capas del datasource.                                 |
| `crear_ID(capa=None, nombreCampo='ID_OGR')`  | Añade un campo ID secuencial.                                              |
| `obtener_objeto_porID(...)`                  | Filtra features por valor de un campo ID.                                  |
| `borrar_geometria(capa=None)`                | Elimina las geometrías (deja solo atributos).                             |
| `añadir_capa(src_capa)`                       | Copia una capa `ogr.Layer` externa al datasource.                         |

---

### 3. Raster_conex — Datos ráster con GDAL

**Archivo:** `conex/Raster_conex.py`  
**Clase:** `FuenteDatosRaster`

Clase para leer y exportar datos ráster usando **GDAL**. Soporta archivos locales, URLs (vía `/vsicurl/`) y ZIP (vía `/vsizip/`).

#### Métodos

| Método                                       | Descripción                                                                 |
|----------------------------------------------|-----------------------------------------------------------------------------|
| `probar_gdal_ogr()` *(static)*               | Diagnóstico: versión de GDAL y lista de drivers.                           |
| `__init__(dato)`                             | Almacena la ruta o URL de la fuente ráster.                                |
| `leer(banda=None, EPSG_Entrada=None, datasetCompleto=True)` | Abre el dataset con `gdal.Open()`. Si se indica `banda`, extrae solo esa banda a un dataset en memoria. Asigna `EPSG_Entrada` si el origen no tiene proyección. |
| `exportar(EPSG_Salida=None, outputFormat='GTiff', WLD=False, PAM=False)` | Con `outputFormat='json'`/`'application/json'` devuelve **CoverageJSON** (OGC API - Coverages). En otro caso exporta con `gdal.Warp` (reproyección, worldfile con `WLD=True`, metadatos PAM con `PAM=True`) y devuelve el archivo como **bytes**; empaqueta en ZIP si hay archivos auxiliares. |
| `propiedades_cobertura()`                    | Metadatos de la cobertura (bbox, CRS, resolución, nº bandas...).           |
| `obtener_atributos(banda=None)`              | Metadatos y estadísticas por banda.                                       |
| `gdalinfo_2_json()`                          | Información estilo `gdalinfo` como dict.                                   |
| `MRE_datos(banda=None, MRE=..., EPSG_MRE=4326)` | Recorta físicamente el ráster al bbox indicado.                        |
| `extraer_bandas(bandas)`                     | Crea un dataset en memoria con las bandas seleccionadas.                   |
| `redimensionar(height=None, width=None)`     | Remuestrea el ráster a nuevas dimensiones.                                 |

---

### 4. Conectores IoT (Sonoff / Tuya)

**Archivos:** `conex/sonoff_conex.py`, `conex/tuyaSmartLife_conex.py`

Exponen dispositivos IoT como capas geográficas. Requieren dependencias adicionales (ver *Instalación*).

**Sonoff/eWeLink** — `infoSonoff` gestiona login contra eWeLink, descubrimiento de dispositivos por mDNS (`zeroconf`) y descifrado del estado (AES-CBC/MD5). Las variantes de fuente de datos combinan `infoSonoff` con utilidades de consulta:

| Clase                       | Salida / base                                                        |
|-----------------------------|---------------------------------------------------------------------|
| `FuenteDatosSonoff`         | Exporta dispositivos a **GeoJSON** desde JSON (`+ geojsonQuery`).    |
| `FuenteDatosSonoff_SQLITE`  | Igual, leyendo desde un **SQLite** de dispositivos.                  |
| `FuenteDatosSonoff_OGR`     | Construye un datasource **OGR** en memoria (`+ FuenteDatosVector`).  |

`geojsonQuery` es un mini-motor de consultas sobre GeoJSON en memoria: `MRE_datos` (bbox), `aplicar_filtro_sql` (filtro SQL-like evaluado de forma **segura** mediante AST, sin `eval`), `ordenar_por`, `limit`, `offset`, `crear_ID`, `obtener_objeto_porID`, `obtenerAtributos`, `borrar_geometria`.

**Tuya Smart Life** — `infoTuyaSmartLife` firma peticiones a Tuya Cloud (HMAC-SHA256), descubre dispositivos locales con `tinytuya`, y permite agruparlos por tipo, guardarlos en SQLite o exportarlos a JSON.

| Clase                       | Salida / base                                                        |
|-----------------------------|----------------------------------------------------------------------|
| `FuenteDatosTuya`           | Exporta dispositivos a **GeoJSON** desde JSON (`+ geojsonQuery`).     |
| `FuenteDatosTuya_SQLITE`    | Igual, leyendo desde un **SQLite** de dispositivos.                  |
| `FuenteDatosTuya_OGR`       | Construye un datasource **OGR** en memoria (`+ FuenteDatosVector`).  |

---

### 5. Procesos vectoriales

**Archivos:** `procesos/vector/geoprocesos.py`, `procesos/vector/tematicos.py`

Funciones OGR que operan sobre objetos `ogr.Layer`:

| Función                                                  | Descripción                                             |
|---------------------------------------------------------|---------------------------------------------------------|
| `crear_capa_buffer_OGR(layer, distancia_buffer, ...)`   | Nueva capa en memoria con el buffer de cada geometría.  |
| `crear_atributo_area_OGR(layer, nombre_capa_salida, ...)`| Nueva capa con un campo de área por geometría.         |

---

## Ejemplos de uso

### Conexión a PostgreSQL

```python
from conex.PG_conex import ConexPG

# Opción 1: pasar parámetros directamente
parametros = {
    'IP': '172.17.0.1',
    'port': '5432',
    'user': 'usuario',
    'pass': 'pass',
    'db': 'postgis'
}
pg = ConexPG(dataJSONcon=parametros)
pg.conex2PG(check=True)

# Ejecutar consultas
resultado = pg.queryPG("SELECT NOW();")
print(resultado)  # [(datetime.datetime(...),)]

resultado2 = pg.queryPG("SELECT version(), PostGIS_Version();")
print(resultado2)

resultado3 = pg.queryPG("""
    SELECT ST_AsText(
        ST_Buffer(ST_SetSRID(ST_MakePoint(-3, 40), 4326), 0.01)
    ) AS wkt_buffer;
""")
print(resultado3)
```

### Datos vectoriales

```python
from conex.Vector_conex import FuenteDatosVector

# Abrir desde WFS
fuente = FuenteDatosVector(
    "http://geostematicos-sigc.juntadeandalucia.es/geoserver/tematicos/"
    "ows?service=WFS&version=1.0.0&request=GetFeature"
    "&typeName=tematicos:Provincias&maxFeatures=50&outputFormat=application/json"
)
fuente.leer()

# Exportar a GeoJSON (dict) — siempre reproyectado a EPSG:4326
geojson = fuente.exportar(outputFormat='application/json')
print("Nº de features:", len(geojson["features"]))

# Exportar a Shapefile reproyectado a EPSG:3857 (devuelve bytes)
shp_bytes = fuente.exportar(EPSG_Salida=3857, outputFormat='ESRI Shapefile')

# También desde WKT directo (requiere EPSG de entrada)
fuente_wkt = FuenteDatosVector("POINT (1120351 741921)")
fuente_wkt.leer(EPSG_Entrada=25830)
print(fuente_wkt.obtener_atributos())
```

### Datos ráster

```python
from conex.Raster_conex import FuenteDatosRaster

# Abrir un GeoTIFF remoto
fuente = FuenteDatosRaster("https://cdn.proj.org/es_ign_egm08-rednap.tif")
fuente.leer()

# Exportar a PNG con worldfile y metadatos PAM
blob = fuente.exportar(EPSG_Salida=25830, outputFormat='PNG', WLD=True, PAM=True)
```

---

## Integración con pygeoapi

Aunque `pygdal_PG_datasource` no implementa directamente la interfaz `BaseProvider` de pygeoapi, proporciona los componentes fundamentales para construir providers personalizados. Un ejemplo de cómo podría integrarse:

```python
# provider_pygdal.py — Ejemplo conceptual
from pygeoapi.provider.base import BaseProvider
from conex.Vector_conex import FuenteDatosVector
from conex.Raster_conex import FuenteDatosRaster

class PyGDALVectorProvider(BaseProvider):
    """Provider pygeoapi para datos vectoriales vía GDAL/OGR."""

    def __init__(self, provider_def):
        super().__init__(provider_def)
        self.fuente = FuenteDatosVector(provider_def['data'])
        self.fuente.leer()

    def query(self, **kwargs):
        # exportar() ya devuelve un dict GeoJSON (no un string)
        return self.fuente.exportar(outputFormat='application/json')

    def get(self, id):
        raise NotImplementedError()
```

Y su correspondiente configuración YAML para pygeoapi:

```yaml
resources:
    provincias:
        type: collection
        title: Provincias
        description: Provincias desde WFS via pygdal_PG_datasource
        providers:
            - type: feature
              name: provider_pygdal.PyGDALVectorProvider
              data: http://geostematicos-sigc.juntadeandalucia.es/geoserver/tematicos/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=tematicos:Provincias&maxFeatures=50&outputFormat=application/json
              format:
                  name: GeoJSON
```

---

## Notas técnicas

### Virtual Filesystem (VSI) de GDAL

La librería hace uso intensivo del sistema de archivos virtual de GDAL:
- **`/vsicurl/`** — acceso transparente a archivos remotos vía HTTP/HTTPS.
- **`/vsizip/`** — lectura directa desde archivos ZIP sin descompresión manual.

### Drivers GDAL/OGR

- **Lectura**: cualquier driver OGR (GeoJSON, Shapefile, GPKG, WFS, MVT, PostgreSQL, etc.) y cualquier driver GDAL (GTiff, JPEG, PNG, etc.)
- **Escritura**: el driver de salida se determina por el parámetro `outputFormat`. Para múltiples capas con drivers que no soportan multicapa, se genera automáticamente un ZIP.

### Estado del desarrollo

> **Alpha** — La API puede cambiar. Actualmente en fase de refactorización: los módulos originales `Imp_Capas.py` / `Exp_Capas.py` han sido reemplazados por el diseño actual orientado a fuentes de datos (`FuenteDatosVector`, `FuenteDatosRaster`), y se han añadido conectores IoT (`sonoff_conex`, `tuyaSmartLife_conex`).

**Correcciones recientes:**
- `PG_conex.queryPG()` ya no pasa `self` a `conex2PG`; abre una conexión propia y libera los recursos con `try/finally`.
- El descubrimiento Tuya expone `find_all_devices()` (usado por `get_devices`) y `discover_tuya_by_id_or_ip()` funciona correctamente.
- `infoSonoff.refreshAT()`/`logout()` usan `self.APP` (antes referenciaban un global inexistente).
- Los constructores de los conectores IoT resuelven correctamente la ruta por defecto cuando no se pasa `ruta_json_params`.
- `geojsonQuery.aplicar_filtro_sql()` evalúa el filtro con un intérprete AST con lista blanca de nodos, eliminando el uso inseguro de `eval`.

---

## Tests

La librería incluye una suite de **pytest** dividida en dos categorías:

- **Unit tests** (`tests/test_*.py`): prueban la lógica pura y usan *mocks* para las
  dependencias externas (psycopg2, tinytuya). No requieren red, base de datos ni
  hardware. Los que necesitan una dependencia opcional (GDAL, pycryptodome) se
  **saltan automáticamente** si no está instalada.
- **Integration tests** (`tests/integration/`): ejercitan recursos reales (WFS/WMS,
  CDNs, PostgreSQL, dispositivos IoT). Reemplazan a los antiguos scripts manuales
  `test/puntero_*.py`. Están marcados con `@pytest.mark.integration` y **desactivados
  por defecto**; se saltan solos si no hay red o credenciales.

### Ejecución

```bash
# Instalar pytest (y opcionalmente gdal/pycryptodome para más cobertura)
pip install -r tests/requirements-test.txt

# Solo unit tests (por defecto; rápido, sin recursos externos)
pytest

# Solo tests de integración (requieren red/credenciales)
pytest -m integration

# Todo
pytest -m "unit or integration"   # equivalente a:  pytest -m ""
```

### Variables de entorno para integración

Los tests de integración con credenciales se saltan salvo que definas:

| Variable                | Test                          |
|-------------------------|-------------------------------|
| `PG_TEST_HOST` / `PG_TEST_PORT` / `PG_TEST_USER` / `PG_TEST_PASS` / `PG_TEST_DB` | PostgreSQL |
| `EWELINK_PARAMS_JSON`   | Sonoff/eWeLink (ruta a un JSON de parámetros válido) |
| `TUYA_PARAMS_JSON`      | Tuya Smart Life (ruta a un JSON de parámetros válido) |

> ⚠️ **Nunca** incluyas credenciales reales en el repositorio. Los ficheros de
> parámetros/estado (`params_*.json`, `devices_*.json`, `*.sqlite`, `PGconex.json`)
> están en `.gitignore`. Pásalos siempre por variables de entorno o rutas locales.

---

## Licencia

[MIT](LICENSE)

---

Desarrollado por [IngenieroGeomatico (A²)](https://github.com/IngenieroGeomatico)
