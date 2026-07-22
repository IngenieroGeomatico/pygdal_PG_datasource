"""
Tests unitarios de ``conex.sonoff_conex.geojsonQuery``.

``geojsonQuery`` es lógica pura sobre diccionarios GeoJSON (no depende de GDAL,
red ni hardware), por lo que estos tests se ejecutan siempre.

Cubren especialmente ``aplicar_filtro_sql``, que se refactorizó para evaluar la
expresión mediante un intérprete AST con lista blanca de nodos, eliminando el
antiguo uso inseguro de ``eval``.
"""
import copy

import pytest

from conex.sonoff_conex import geojsonQuery


def _geojson_ejemplo():
    """FeatureCollection de puntos con propiedades numéricas y de texto."""
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [0.0, 0.0]},
                "properties": {"nombre": "a", "temp": 10, "on": True},
            },
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [5.0, 5.0]},
                "properties": {"nombre": "b", "temp": 25, "on": False},
            },
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [50.0, 50.0]},
                "properties": {"nombre": "c", "temp": 40, "on": True},
            },
        ],
    }


@pytest.fixture
def q():
    consulta = geojsonQuery()
    consulta.geojson = _geojson_ejemplo()
    return consulta


# --------------------------------------------------------------------------- #
# aplicar_filtro_sql — funcionalidad
# --------------------------------------------------------------------------- #
class TestAplicarFiltroSql:
    def test_comparacion_mayor(self, q):
        resultado = q.aplicar_filtro_sql("temp > 20")
        nombres = [f["properties"]["nombre"] for f in resultado["features"]]
        assert nombres == ["b", "c"]

    def test_igualdad_convierte_un_solo_igual(self, q):
        resultado = q.aplicar_filtro_sql("temp = 25")
        assert len(resultado["features"]) == 1
        assert resultado["features"][0]["properties"]["nombre"] == "b"

    def test_and(self, q):
        resultado = q.aplicar_filtro_sql("temp >= 10 AND temp <= 25")
        nombres = [f["properties"]["nombre"] for f in resultado["features"]]
        assert nombres == ["a", "b"]

    def test_or(self, q):
        resultado = q.aplicar_filtro_sql("temp < 15 OR temp > 35")
        nombres = [f["properties"]["nombre"] for f in resultado["features"]]
        assert nombres == ["a", "c"]

    def test_not(self, q):
        resultado = q.aplicar_filtro_sql("NOT temp = 25")
        nombres = [f["properties"]["nombre"] for f in resultado["features"]]
        assert nombres == ["a", "c"]

    def test_operadores_case_insensitive(self, q):
        resultado = q.aplicar_filtro_sql("temp >= 10 and temp <= 25")
        assert len(resultado["features"]) == 2

    def test_parentesis(self, q):
        resultado = q.aplicar_filtro_sql("(temp = 10 OR temp = 40) AND NOT temp = 25")
        nombres = [f["properties"]["nombre"] for f in resultado["features"]]
        assert nombres == ["a", "c"]

    def test_muta_estado_interno(self, q):
        q.aplicar_filtro_sql("temp > 20")
        assert len(q.geojson["features"]) == 2

    def test_sin_geojson_lanza(self):
        consulta = geojsonQuery()
        consulta.geojson = None
        with pytest.raises(Exception):
            consulta.aplicar_filtro_sql("temp > 20")


# --------------------------------------------------------------------------- #
# aplicar_filtro_sql — seguridad (regresión del fix de RCE)
# --------------------------------------------------------------------------- #
class TestFiltroSqlSeguridad:
    def test_no_ejecuta_codigo_arbitrario(self, q):
        """Una llamada a función debe ser rechazada por el evaluador AST.

        Con el antiguo ``eval`` esto habría intentado ejecutar código; ahora la
        expresión no es válida y el feature simplemente no pasa el filtro (la
        excepción interna se captura por feature), resultando en 0 features.
        """
        resultado = q.aplicar_filtro_sql("__import__('os')")
        assert resultado["features"] == []

    def test_expresion_no_valida_no_rompe(self, q):
        # Sintaxis Python inválida -> ValueError controlado
        with pytest.raises(ValueError):
            q.aplicar_filtro_sql("temp >>>")

    def test_acceso_atributos_rechazado(self, q):
        resultado = q.aplicar_filtro_sql("temp.__class__ = 1")
        assert resultado["features"] == []


# --------------------------------------------------------------------------- #
# MRE_datos (filtro por bounding box)
# --------------------------------------------------------------------------- #
class TestMREDatos:
    def test_bbox_filtra_puntos(self, q):
        resultado = q.MRE_datos(MRE=[-1, -1, 10, 10])
        nombres = [f["properties"]["nombre"] for f in resultado["features"]]
        assert nombres == ["a", "b"]

    def test_bbox_incluye_todos(self, q):
        resultado = q.MRE_datos(MRE=[-100, -100, 100, 100])
        assert len(resultado["features"]) == 3

    def test_bbox_excluye_todos(self, q):
        resultado = q.MRE_datos(MRE=[100, 100, 200, 200])
        assert resultado["features"] == []


# --------------------------------------------------------------------------- #
# ordenar_por
# --------------------------------------------------------------------------- #
class TestOrdenarPor:
    def test_ascendente(self, q):
        resultado = q.ordenar_por("nombre", orden="asc")
        nombres = [f["properties"]["nombre"] for f in resultado["features"]]
        assert nombres == ["a", "b", "c"]

    def test_descendente(self, q):
        resultado = q.ordenar_por("nombre", orden="desc")
        nombres = [f["properties"]["nombre"] for f in resultado["features"]]
        assert nombres == ["c", "b", "a"]


# --------------------------------------------------------------------------- #
# limit / offset
# --------------------------------------------------------------------------- #
class TestLimitOffset:
    def test_limit(self, q):
        resultado = q.limit(2)
        assert len(resultado["features"]) == 2

    def test_offset(self, q):
        resultado = q.offset(1)
        nombres = [f["properties"]["nombre"] for f in resultado["features"]]
        assert nombres == ["b", "c"]

    def test_offset_y_limit_encadenados(self, q):
        q.offset(1)
        resultado = q.limit(1)
        assert len(resultado["features"]) == 1
        assert resultado["features"][0]["properties"]["nombre"] == "b"


# --------------------------------------------------------------------------- #
# crear_ID / obtener_objeto_porID
# --------------------------------------------------------------------------- #
class TestID:
    def test_crear_id_secuencial(self, q):
        resultado = q.crear_ID(nombreCampo="ID_OGR")
        ids = [f["properties"]["ID_OGR"] for f in resultado["features"]]
        assert ids == [0, 1, 2]
        # También se refleja en feature["id"]
        assert [f["id"] for f in resultado["features"]] == [0, 1, 2]

    def test_obtener_objeto_por_id(self, q):
        q.crear_ID(nombreCampo="ID_OGR")
        resultado = q.obtener_objeto_porID(ID="ID_OGR", valorID=1)
        assert len(resultado["features"]) == 1
        assert resultado["features"][0]["properties"]["nombre"] == "b"

    def test_obtener_objeto_por_id_inexistente(self, q):
        q.crear_ID(nombreCampo="ID_OGR")
        resultado = q.obtener_objeto_porID(ID="ID_OGR", valorID=99)
        assert resultado is None


# --------------------------------------------------------------------------- #
# obtener_atributos / obtenerAtributos / borrar_geometria
# --------------------------------------------------------------------------- #
class TestAtributos:
    def test_obtener_atributos_infiere_tipos(self, q):
        atributos = q.obtener_atributos()
        assert atributos["nombre"] == {"type": "string"}
        assert atributos["temp"] == {"type": "integer"}
        assert atributos["on"] == {"type": "boolean"}

    def test_obtener_atributos_generaliza_tipos_mixtos(self):
        consulta = geojsonQuery()
        consulta.geojson = {
            "type": "FeatureCollection",
            "features": [
                {"properties": {"x": 1}},
                {"properties": {"x": "texto"}},
            ],
        }
        atributos = consulta.obtener_atributos()
        assert atributos["x"]["type"] == "string"

    def test_obtenerAtributos_proyecta_campos(self, q):
        resultado = q.obtenerAtributos(["nombre"])
        primera = resultado["features"][0]
        assert set(primera.keys()) == {"nombre"}

    def test_borrar_geometria(self, q):
        original = copy.deepcopy(q.geojson)
        resultado = q.borrar_geometria()
        # Ya no quedan claves de geometría en los features resultantes
        for f in resultado["features"]:
            assert "geometry" not in f
        assert len(resultado["features"]) == len(original["features"])
