# pygdal_PG_datasource

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![GDAL](https://img.shields.io/badge/GDAL-3.0%2B-green)
![License](https://img.shields.io/badge/license-MIT-yellow)
![Status](https://img.shields.io/badge/status-alpha-orange)

**Acceso unificado a datos geoespaciales vectoriales y ráster vía GDAL/OGR, con conexión a PostgreSQL/PostGIS.**

`pygdal_PG_datasource` es una librería Python que abstrae el acceso a fuentes de datos geográficos mediante **GDAL/OGR** y la conexión a bases de datos **PostgreSQL/PostGIS** mediante **psycopg2**. Está diseñada para servir como capa de datos en proyectos que necesiten leer, transformar y exportar información geoespacial desde múltiples orígenes (archivos locales, WFS, WMS, MVT, WKT, GeoJSON embebido, PostGIS, etc.).

> Este repositorio es un submódulo de [pygeoapi_complementos](https://github.com/IngenieroGeomatico/pygeoapi_complementos), que a su vez es un submódulo de [pygeoapi_plus](https://github.com/IngenieroGeomatico/pygeoapi_plus). Su propósito es proporcionar los bloques fundamentales de acceso a datos para una futura integración con **pygeoapi**.

---

## Estructura del repositorio

```
pygdal_PG_datasource/
├── lib/
│   ├── PG_conex.py        # Conexión y consultas a PostgreSQL (psycopg2)
│   ├── Vector_conex.py     # Lectura y exportación de datos vectoriales (OGR)
│   └── Raster_conex.py     # Lectura y exportación de datos ráster (GDAL)
├── test/
│   ├── puntero_PG.py       # Ejemplo de uso de PG_conex
│   ├── puntero_vector.py   # Ejemplo de uso de Vector_conex
│   └── puntero_raster.py   # Ejemplo de uso de Raster_conex
├── tmp/                    # Directorio temporal para exportaciones
└── README.md
```

---

## Requisitos

- **Python** 3.8 o superior
- **GDAL/OGR** 3.0 o superior (`python3-gdal` o `gdal` vía pip)
- **psycopg2** (`psycopg2` o `psycopg2-binary`) — solo necesario para el módulo `PG_conex`

### Instalación de dependencias

```bash
# Con pip
pip install gdal psycopg2-binary

# En Debian/Ubuntu
sudo apt install python3-gdal python3-psycopg2

# En entornos Conda
conda install -c conda-forge gdal psycopg2
```

---

## Instalación

Actualmente la librería se usa por copia directa del directorio `lib/`:

```bash
git clone https://github.com/IngenieroGeomatico/pygdal_PG_datasource.git
cd pygdal_PG_datasource
```

No requiere `pip install`. Para usar los módulos desde tu proyecto:

```python
import sys
sys.path.insert(0, '/ruta/a/pygdal_PG_datasource')

from lib.PG_conex import ConexPG
from lib.Vector_conex import FuenteDatosVector
from lib.Raster_conex import FuenteDatosRaster
```

---

## Módulos

### 1. PG_conex — Conexión PostgreSQL

**Archivo:** `lib/PG_conex.py`  
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
| `conex2PG(check=False)`              | Establece conexión a PostgreSQL. Si `check=True`, abre y cierra la conexión (modo verificación). Si `check=False`, retorna el objeto `connection`. |
| `queryPG(query)`                     | Ejecuta una consulta SQL (`SELECT`) y retorna los resultados con `fetchall()`. |

---

### 2. Vector_conex — Datos vectoriales con OGR

**Archivo:** `lib/Vector_conex.py`  
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

#### Métodos

| Método                                       | Descripción                                                                 |
|----------------------------------------------|-----------------------------------------------------------------------------|
| `probar_gdal_ogr()` *(static)*               | Diagnóstico: muestra la versión de GDAL y lista los drivers vectoriales y ráster disponibles. |
| `__init__(dato)`                             | Almacena la ruta/URL/WKT de la fuente de datos.                            |
| `leer(capa=None, EPSG_Entrada=None, AllLayers=False)` | Abre la fuente y la copia a un datasource en memoria (driver MEMORY). Si `AllLayers=True`, retorna el datasource completo. Para URLs HTTP antepone `/vsicurl/`; para ZIP, `/vsizip/`. WKT se convierte en un layer en memoria. |
| `exportar(EPSG_Salida=None, outputFormat='application/json')` | Exporta la capa a GeoJSON (por defecto) o a cualquier formato soportado por OGR (Shapefile, GPKG, etc.). Si hay varias capas y el driver no soporta multicapa, crea archivos separados y los empaqueta en ZIP. Soporta reproyección. |
| `obtener_atributos(capa=None)`               | Retorna un diccionario con los nombres de campo y sus tipos para una capa o todas las capas. |

---

### 3. Raster_conex — Datos ráster con GDAL

**Archivo:** `lib/Raster_conex.py`  
**Clase:** `FuenteDatosRaster`

Clase para leer y exportar datos ráster usando **GDAL**. Soporta archivos locales, URLs (vía `/vsicurl/`) y ZIP (vía `/vsizip/`).

#### Métodos

| Método                                       | Descripción                                                                 |
|----------------------------------------------|-----------------------------------------------------------------------------|
| `probar_gdal_ogr()` *(static)*               | Diagnóstico: versión de GDAL y lista de drivers.                           |
| `__init__(dato)`                             | Almacena la ruta o URL de la fuente ráster.                                |
| `leer(banda=None, EPSG_Entrada=None)`        | Abre el dataset ráster con `gdal.Open()`.                                  |
| `exportar(EPSG_Salida=None, outputFormat='GTiff', WLD=False, PAM=False)` | Exporta usando `gdal.Warp`. Soporta reproyección, worldfile (`WLD=True`) y metadatos PAM. Si hay múltiples archivos asociados, los comprime en ZIP. |

---

## Ejemplos de uso

### Conexión a PostgreSQL

```python
from lib.PG_conex import ConexPG

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
from lib.Vector_conex import FuenteDatosVector

# Abrir desde WFS
fuente = FuenteDatosVector(
    "http://geostematicos-sigc.juntadeandalucia.es/geoserver/tematicos/"
    "ows?service=WFS&version=1.0.0&request=GetFeature"
    "&typeName=tematicos:Provincias&maxFeatures=50&outputFormat=application/json"
)
fuente.leer()

# Exportar a GeoJSON reproyectado a EPSG:3857
geojson = fuente.exportar(EPSG_Salida=3857, outputFormat='application/json')
print(geojson[:200])

# También desde WKT directo
fuente_wkt = FuenteDatosVector("POINT (1120351 741921)")
fuente_wkt.leer(EPSG_Entrada=25830)
print(fuente_wkt.obtener_atributos())
```

### Datos ráster

```python
from lib.Raster_conex import FuenteDatosRaster

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
from lib.Vector_conex import FuenteDatosVector
from lib.Raster_conex import FuenteDatosRaster

class PyGDALVectorProvider(BaseProvider):
    """Provider pygeoapi para datos vectoriales vía GDAL/OGR."""

    def __init__(self, provider_def):
        super().__init__(provider_def)
        self.fuente = FuenteDatosVector(provider_def['data'])
        self.fuente.leer()

    def query(self, **kwargs):
        geojson_str = self.fuente.exportar(EPSG_Salida=4326)
        return json.loads(geojson_str)

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

> **Alpha** — La API puede cambiar. Actualmente en fase de refactorización: los módulos originales `Imp_Capas.py` / `Exp_Capas.py` han sido reemplazados por el diseño actual orientado a fuentes de datos (`FuenteDatosVector`, `FuenteDatosRaster`).

**Problemas conocidos:**
- En `PG_conex.py:121`, `self.conex2PG(self)` pasa el objeto `self` como argumento posicional, pero el método espera un booleano (`check=False`). *Pendiente de corregir.*
- El directorio `lib/` no contiene `__init__.py`, por lo que no es un paquete Python formal.
- No hay tests automatizados (los archivos en `test/` son scripts de prueba manuales).

---

## Licencia

[MIT](LICENSE)

---

Desarrollado por [IngenieroGeomatico (A²)](https://github.com/IngenieroGeomatico)
