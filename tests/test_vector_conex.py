"""
Tests unitarios de ``conex.Vector_conex.FuenteDatosVector``.

Requieren GDAL/OGR (paquete ``osgeo``). Si no está instalado, todos los tests de
este módulo se saltan limpiamente. Se usan entradas en memoria (WKT y GeoJSON
embebido) para no depender de red ni de archivos externos.
"""
import json
import os

import pytest

# Salta todo el módulo si GDAL no está disponible.
pytest.importorskip("osgeo", reason="GDAL/OGR (osgeo) no instalado")

from osgeo import ogr  # noqa: E402

from conex.Vector_conex import FuenteDatosVector  # noqa: E402


GEOJSON_PUNTOS = json.dumps(
    {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"nombre": "uno", "valor": 10},
                "geometry": {"type": "Point", "coordinates": [-3.7, 40.4]},
            },
            {
                "type": "Feature",
                "properties": {"nombre": "dos", "valor": 20},
                "geometry": {"type": "Point", "coordinates": [2.1, 41.4]},
            },
        ],
    }
)


class TestLeerWKT:
    def test_leer_wkt_crea_datasource(self):
        fuente = FuenteDatosVector("POINT (440000 4474000)")
        ds = fuente.leer(EPSG_Entrada=25830)
        assert ds is not None
        assert ds.GetLayerCount() == 1

    def test_leer_wkt_sin_epsg_lanza(self):
        fuente = FuenteDatosVector("POINT (440000 4474000)")
        with pytest.raises(Exception):
            fuente.leer()


class TestLeerGeoJSON:
    def test_leer_geojson_embebido(self):
        fuente = FuenteDatosVector(GEOJSON_PUNTOS)
        ds = fuente.leer()
        assert ds is not None
        capa = ds.GetLayerByIndex(0)
        assert capa.GetFeatureCount() == 2

    def test_obtener_capas(self):
        fuente = FuenteDatosVector(GEOJSON_PUNTOS)
        fuente.leer()
        capas = fuente.obtener_capas()
        assert len(capas) == 1

    def test_obtener_atributos(self):
        fuente = FuenteDatosVector(GEOJSON_PUNTOS)
        fuente.leer()
        atributos = fuente.obtener_atributos()
        # Un único layer; sus campos incluyen nombre (string) y valor (numérico)
        (campos,) = atributos.values()
        assert campos["nombre"]["type"] == "string"
        assert campos["valor"]["type"] in ("integer", "number")


class TestExportarGeoJSON:
    def test_exportar_json_devuelve_dict(self):
        fuente = FuenteDatosVector(GEOJSON_PUNTOS)
        fuente.leer()
        salida = fuente.exportar(outputFormat="application/json")
        assert isinstance(salida, dict)
        assert salida["type"] == "FeatureCollection"
        assert len(salida["features"]) == 2

    def test_exportar_json_reproyecta_a_4326(self):
        # Entrada en EPSG:25830; la salida GeoJSON debe estar en grados (EPSG:4326).
        fuente = FuenteDatosVector("POINT (440000 4474000)")
        fuente.leer(EPSG_Entrada=25830)
        salida = fuente.exportar(outputFormat="application/json")
        coords = salida["features"][0]["geometry"]["coordinates"]
        # Longitud/latitud plausibles para la Península Ibérica.
        assert -10 < coords[0] < 5
        assert 35 < coords[1] < 44


class TestCrearID:
    def test_crear_id_secuencial(self):
        fuente = FuenteDatosVector(GEOJSON_PUNTOS)
        fuente.leer()
        capa = fuente.crear_ID(nombreCampo="ID_OGR")
        capa.ResetReading()
        ids = sorted(feat.GetField("ID_OGR") for feat in capa)
        assert ids == [0, 1]


# --------------------------------------------------------------------------- #
# Lectura desde archivo SQLite real (tests/files/)
# --------------------------------------------------------------------------- #
class TestLeerSQLite:
    """Abre devices_sonoff.sqlite como datasource OGR (mediante driver SQLite)."""

    @pytest.fixture(scope="class")
    def sqlite_path(self):
        return os.path.join(
            os.path.dirname(__file__), "files", "devices_sonoff.sqlite"
        )

    def test_abrir_sqlite_como_ogr(self, sqlite_path):
        ds = ogr.Open(sqlite_path)
        assert ds is not None
        assert ds.GetLayerCount() >= 2

    def test_leer_capa_sqlite(self, sqlite_path):
        fuente = FuenteDatosVector(sqlite_path)
        ds = fuente.leer(datasetCompleto=True)
        assert ds is not None
        capas = [ds.GetLayerByIndex(i).GetName() for i in range(ds.GetLayerCount())]
        assert set(capas).issuperset({"MINIR4", "DUALR3"})

    def test_leer_capa_especifica_sqlite(self, sqlite_path):
        fuente = FuenteDatosVector(sqlite_path)
        ds = fuente.leer(capa="MINIR4")
        assert ds is not None
        capa = ds.GetLayerByIndex(0)
        assert capa.GetName() == "MINIR4"
        assert capa.GetFeatureCount() >= 2
        # Verificar que los campos esperados existen
        defn = capa.GetLayerDefn()
        campos = {defn.GetFieldDefn(i).GetName() for i in range(defn.GetFieldCount())}
        assert campos.issuperset({"id", "extra", "state"})

    def test_atributos_sqlite(self, sqlite_path):
        fuente = FuenteDatosVector(sqlite_path)
        fuente.leer(capa="DUALR3")
        atributos = fuente.obtener_atributos()
        (campos,) = atributos.values()
        assert campos["id"]["type"] == "string"

    def test_exportar_json_sqlite(self, sqlite_path):
        fuente = FuenteDatosVector(sqlite_path)
        fuente.leer(capa="MINIR4")
        salida = fuente.exportar(outputFormat="application/json")
        assert isinstance(salida, dict)
        assert salida["type"] == "FeatureCollection"
        assert len(salida["features"]) >= 2
        # Las features de tablas sin geometría se exportan sin "geometry"
        primer_feature = salida["features"][0]
        assert "geometry" not in primer_feature or primer_feature["geometry"] is None
        assert "properties" in primer_feature
