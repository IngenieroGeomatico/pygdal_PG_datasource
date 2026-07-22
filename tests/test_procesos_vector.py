"""
Tests unitarios de ``procesos.vector`` (geoprocesos y temáticos).

Requieren GDAL/OGR (paquete ``osgeo``). Si no está instalado, se saltan.
Se construye una capa en memoria para no depender de archivos externos.
"""
import pytest

pytest.importorskip("osgeo", reason="GDAL/OGR (osgeo) no instalado")

from osgeo import ogr, osr  # noqa: E402

from procesos.vector.geoprocesos import crear_capa_buffer_OGR  # noqa: E402
from procesos.vector.tematicos import crear_atributo_area_OGR  # noqa: E402


@pytest.fixture
def capa_puntos():
    """Capa en memoria con dos puntos en EPSG:25830 (metros)."""
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(25830)

    driver = ogr.GetDriverByName("Memory")
    ds = driver.CreateDataSource("in")
    layer = ds.CreateLayer("puntos", srs=srs, geom_type=ogr.wkbPoint)
    layer.CreateField(ogr.FieldDefn("nombre", ogr.OFTString))

    for i, (x, y) in enumerate([(440000, 4474000), (441000, 4475000)]):
        feat = ogr.Feature(layer.GetLayerDefn())
        geom = ogr.Geometry(ogr.wkbPoint)
        geom.AddPoint(x, y)
        feat.SetGeometry(geom)
        feat.SetField("nombre", f"p{i}")
        layer.CreateFeature(feat)
        feat = None

    # Mantener ds vivo mientras dure el test.
    yield ds, layer


@pytest.fixture
def capa_poligono():
    """Capa en memoria con un polígono cuadrado de 100x100 m en EPSG:25830."""
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(25830)

    driver = ogr.GetDriverByName("Memory")
    ds = driver.CreateDataSource("in_pol")
    layer = ds.CreateLayer("pol", srs=srs, geom_type=ogr.wkbPolygon)
    layer.CreateField(ogr.FieldDefn("nombre", ogr.OFTString))

    wkt = "POLYGON ((0 0, 0 100, 100 100, 100 0, 0 0))"
    feat = ogr.Feature(layer.GetLayerDefn())
    feat.SetGeometry(ogr.CreateGeometryFromWkt(wkt))
    feat.SetField("nombre", "cuadrado")
    layer.CreateFeature(feat)
    feat = None

    yield ds, layer


class TestBuffer:
    def test_buffer_genera_poligonos(self, capa_puntos):
        _, layer = capa_puntos
        ds_buffer, buffer_layer = crear_capa_buffer_OGR(layer, 50.0)
        assert buffer_layer.GetGeomType() == ogr.wkbPolygon
        assert buffer_layer.GetFeatureCount() == 2

    def test_buffer_conserva_atributos(self, capa_puntos):
        _, layer = capa_puntos
        ds_buffer, buffer_layer = crear_capa_buffer_OGR(layer, 10.0)
        buffer_layer.ResetReading()
        nombres = sorted(feat.GetField("nombre") for feat in buffer_layer)
        assert nombres == ["p0", "p1"]


class TestArea:
    def test_calcula_area(self, capa_poligono):
        _, layer = capa_poligono
        ds_area, area_layer = crear_atributo_area_OGR(layer, "con_area", "area_m2")
        area_layer.ResetReading()
        feat = next(iter(area_layer))
        assert feat.GetField("area_m2") == pytest.approx(10000.0, rel=1e-6)

    def test_conserva_atributos_originales(self, capa_poligono):
        _, layer = capa_poligono
        ds_area, area_layer = crear_atributo_area_OGR(layer, "con_area", "area_m2")
        area_layer.ResetReading()
        feat = next(iter(area_layer))
        assert feat.GetField("nombre") == "cuadrado"
