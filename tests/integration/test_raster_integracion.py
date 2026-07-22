"""
Tests de INTEGRACIÓN de ``FuenteDatosRaster`` (sustituyen a test/puntero_raster.py).

Leen un GeoTIFF público remoto vía /vsicurl/ y lo exportan. Se saltan si no hay
red o GDAL.

Ejecutar solo estos:  pytest -m integration tests/integration/test_raster_integracion.py
"""
import pytest

from tests.integration.helpers import requiere_red, requiere_gdal

pytestmark = [pytest.mark.integration, requiere_gdal, requiere_red]


# GeoTIFF público usado por el antiguo puntero_raster.py
URL_TIF = "https://cdn.proj.org/es_ign_egm08-rednap.tif"


def test_leer_geotiff_remoto():
    from conex.Raster_conex import FuenteDatosRaster

    fuente = FuenteDatosRaster(URL_TIF)
    ds = fuente.leer()
    assert ds is not None
    assert ds.RasterXSize > 0
    assert ds.RasterYSize > 0
    assert ds.RasterCount >= 1


def test_propiedades_cobertura():
    from conex.Raster_conex import FuenteDatosRaster

    fuente = FuenteDatosRaster(URL_TIF)
    fuente.leer()
    props = fuente.propiedades_cobertura()
    assert "bbox" in props
    assert len(props["bbox"]) == 4
    assert props["width"] > 0 and props["height"] > 0


def test_exportar_png_reproyectado():
    from conex.Raster_conex import FuenteDatosRaster

    fuente = FuenteDatosRaster(URL_TIF)
    fuente.leer(EPSG_Entrada=3857)
    blob = fuente.exportar(
        EPSG_Salida=25830, outputFormat="PNG", WLD=True, PAM=True
    )
    assert isinstance(blob, (bytes, bytearray))
    assert len(blob) > 0
