"""
Tests de INTEGRACIÓN de ``FuenteDatosVector`` (sustituyen a test/puntero_vector.py).

Ejercitan lectura desde servicios/archivos remotos reales vía el sistema de
ficheros virtual de GDAL (/vsicurl/, /vsizip/). Se saltan si no hay red o GDAL.

Ejecutar solo estos:  pytest -m integration tests/integration/test_vector_integracion.py
"""
import pytest

from tests.integration.helpers import requiere_red, requiere_gdal

pytestmark = [pytest.mark.integration, requiere_gdal, requiere_red]


# URLs públicas usadas por el antiguo puntero_vector.py
URL_WFS = (
    "http://geostematicos-sigc.juntadeandalucia.es/geoserver/tematicos/"
    "ows?service=WFS&version=1.0.0&request=GetFeature"
    "&typeName=tematicos:Provincias&maxFeatures=50&outputFormat=application/json"
)
URL_ZIP = (
    "https://www.juntadeandalucia.es/institutodeestadisticaycartografia/"
    "dega/sites/default/files/datos/094-dera-1-relieve.zip"
)


def test_leer_wfs_y_exportar_geojson():
    from conex.Vector_conex import FuenteDatosVector

    fuente = FuenteDatosVector(URL_WFS)
    fuente.leer()
    salida = fuente.exportar(EPSG_Salida=4326, outputFormat="application/json")

    assert isinstance(salida, dict)
    assert salida["type"] == "FeatureCollection"
    assert len(salida["features"]) > 0


def test_leer_wfs_atributos():
    from conex.Vector_conex import FuenteDatosVector

    fuente = FuenteDatosVector(URL_WFS)
    fuente.leer()
    atributos = fuente.obtener_atributos()
    assert isinstance(atributos, dict)
    assert len(atributos) >= 1


def test_leer_zip_remoto_vsizip():
    from conex.Vector_conex import FuenteDatosVector

    fuente = FuenteDatosVector(URL_ZIP)
    ds = fuente.leer(capa=0)
    assert ds is not None
    assert ds.GetLayerCount() >= 1


def test_wkt_leer_y_exportar():
    """No requiere red, pero se mantiene junto al flujo de integración vector."""
    from conex.Vector_conex import FuenteDatosVector

    fuente = FuenteDatosVector("POINT (440000 4474000)")
    fuente.leer(EPSG_Entrada=25830)
    salida = fuente.exportar(outputFormat="application/json")
    assert salida["type"] == "FeatureCollection"
    assert len(salida["features"]) == 1
