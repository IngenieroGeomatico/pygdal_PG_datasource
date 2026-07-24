import json
import os
import sqlite3

import pytest

from conex.sonoff_conex import geojsonQuery
from conex.tuyaSmartLife_conex import (
    FuenteDatosTuya,
    FuenteDatosTuya_OGR,
    FuenteDatosTuya_SQLITE,
    infoTuyaSmartLife,
)

FILES_DIR = os.path.join(os.path.dirname(__file__), "files")


# --------------------------------------------------------------------------- #
# Fixtures compartidas
# --------------------------------------------------------------------------- #
@pytest.fixture
def params_tuya_tmp(tmp_path):
    params = {
        "router": {"IP": "", "SSID": "", "pass": ""},
        "tuyaSmartLife": {
            "user_": "test@example.com",
            "password": "test_password",
            "url": "https://developer.tuya.com/",
            "user": {"AccessID": "test_access_id", "AccessSecret": "test_access_secret"},
        },
    }
    ruta = tmp_path / "params_tuya_test.json"
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(params, f)
    return ruta


@pytest.fixture
def tuya_devices_con_coordenadas(tmp_path):
    """Crea un JSON de dispositivos Tuya con coordenadas para probar exportación."""
    dispositivos = {
        "device_001": {
            "extra": {"long": -3.703, "lat": 40.416},
            "tuyaSmartLife": {
                "id": "device_001",
                "name": "Sensor Temp 1",
                "category": "wsdcg",
                "isOnline": True,
            },
            "state": [{"code": "va_temperature", "value": 22.5}],
        },
        "device_002": {
            "extra": {"long": -0.417, "lat": 39.433},
            "tuyaSmartLife": {
                "id": "device_002",
                "name": "Sensor Temp 2",
                "category": "wsdcg",
                "isOnline": True,
            },
            "state": [{"code": "va_temperature", "value": 18.3}],
        },
        "device_003": {
            "extra": {"long": 2.173, "lat": 41.385},
            "tuyaSmartLife": {
                "id": "device_003",
                "name": "Smart Plug",
                "category": "kg",
                "isOnline": True,
            },
            "state": [{"code": "switch_1", "value": True}],
        },
    }
    ruta = tmp_path / "devices_tuya_test.json"
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(dispositivos, f)
    return ruta


@pytest.fixture
def tuya_devices_sqlite(tmp_path, tuya_devices_con_coordenadas):
    """Crea un SQLite con dispositivos Tuya a partir del JSON de prueba."""
    with open(tuya_devices_con_coordenadas) as f:
        dispositivos = json.load(f)
    ruta_sqlite = tmp_path / "devices_tuya_test.sqlite"
    conn = sqlite3.connect(str(ruta_sqlite))
    c = conn.cursor()
    for device_id, device_data in dispositivos.items():
        categoria = device_data["tuyaSmartLife"]["category"]
        c.execute(f"""
            CREATE TABLE IF NOT EXISTS {categoria} (
                id TEXT PRIMARY KEY, extra TEXT, tuyaSmartLife TEXT, state TEXT
            )
        """)
        extra = json.dumps(device_data.get("extra", {}))
        raw = json.dumps(device_data.get("tuyaSmartLife", {}))
        state = json.dumps(device_data.get("state", []))
        c.execute(f"INSERT OR REPLACE INTO {categoria} VALUES (?, ?, ?, ?)",
                  (device_id, extra, raw, state))
    conn.commit()
    conn.close()
    return ruta_sqlite


# --------------------------------------------------------------------------- #
# Tests: FuenteDatosTuya (JSON → GeoJSON)
# --------------------------------------------------------------------------- #
class TestFuenteDatosTuya:
    def test_init_y_capas(self, params_tuya_tmp, tuya_devices_con_coordenadas):
        fuente = FuenteDatosTuya(str(params_tuya_tmp), str(tuya_devices_con_coordenadas))
        assert fuente.capas is not None
        assert "wsdcg" in fuente.capas
        assert "kg" in fuente.capas

    def test_leer_sin_parametros(self, params_tuya_tmp, tuya_devices_con_coordenadas):
        fuente = FuenteDatosTuya(str(params_tuya_tmp), str(tuya_devices_con_coordenadas))
        resultado = fuente.leer()
        assert resultado is not None
        assert any(len(v) > 0 for v in resultado.values())

    def test_leer_por_capa(self, params_tuya_tmp, tuya_devices_con_coordenadas):
        fuente = FuenteDatosTuya(str(params_tuya_tmp), str(tuya_devices_con_coordenadas))
        resultado = fuente.leer(capa="wsdcg")
        assert "wsdcg" in resultado
        assert len(resultado["wsdcg"]) == 2

    def test_leer_dataset_completo(self, params_tuya_tmp, tuya_devices_con_coordenadas):
        fuente = FuenteDatosTuya(str(params_tuya_tmp), str(tuya_devices_con_coordenadas))
        resultado = fuente.leer(datasetCompleto=True)
        assert "wsdcg" in resultado
        assert "kg" in resultado

    def test_exportar_geojson(self, params_tuya_tmp, tuya_devices_con_coordenadas):
        fuente = FuenteDatosTuya(str(params_tuya_tmp), str(tuya_devices_con_coordenadas))
        fuente.leer(capa="wsdcg")
        geojson = fuente.exportar_geojson()
        assert geojson["type"] == "FeatureCollection"
        assert len(geojson["features"]) == 2
        for feat in geojson["features"]:
            assert feat["geometry"]["type"] == "Point"
            assert feat["geometry"]["coordinates"][0] != 0

    def test_exportar_geojson_con_indice(self, params_tuya_tmp, tuya_devices_con_coordenadas):
        fuente = FuenteDatosTuya(str(params_tuya_tmp), str(tuya_devices_con_coordenadas))
        fuente.leer(capa=0)
        geojson = fuente.exportar_geojson(capa=0)
        assert len(geojson["features"]) > 0

    def test_exportar_geojson_sin_coordenadas_se_omite(self, params_tuya_tmp, tmp_path):
        dispositivos = {
            "device_no_coord": {
                "extra": {"long": None, "lat": None},
                "tuyaSmartLife": {"id": "device_no_coord", "name": "No coord", "category": "test"},
                "state": [],
            }
        }
        ruta = tmp_path / "devices_no_coord.json"
        with open(ruta, "w") as f:
            json.dump(dispositivos, f)
        fuente = FuenteDatosTuya(str(params_tuya_tmp), str(ruta))
        fuente.leer(capa="test")
        geojson = fuente.exportar_geojson()
        assert len(geojson["features"]) == 0

    def test_hereda_geojson_query(self, params_tuya_tmp, tuya_devices_con_coordenadas):
        fuente = FuenteDatosTuya(str(params_tuya_tmp), str(tuya_devices_con_coordenadas))
        assert isinstance(fuente, geojsonQuery)
        assert hasattr(fuente, "MRE_datos")
        assert hasattr(fuente, "crear_ID")


# --------------------------------------------------------------------------- #
# Tests: FuenteDatosTuya_SQLITE (SQLite → GeoJSON)
# --------------------------------------------------------------------------- #
class TestFuenteDatosTuyaSQLITE:
    def test_init(self, params_tuya_tmp, tuya_devices_sqlite):
        fuente = FuenteDatosTuya_SQLITE(str(params_tuya_tmp), str(tuya_devices_sqlite))
        assert fuente.capas is not None
        assert "wsdcg" in fuente.capas

    def test_leer_sin_parametros(self, params_tuya_tmp, tuya_devices_sqlite):
        fuente = FuenteDatosTuya_SQLITE(str(params_tuya_tmp), str(tuya_devices_sqlite))
        resultado = fuente.leer()
        assert isinstance(resultado, dict)
        assert "wsdcg" in resultado

    def test_leer_por_capa(self, params_tuya_tmp, tuya_devices_sqlite):
        fuente = FuenteDatosTuya_SQLITE(str(params_tuya_tmp), str(tuya_devices_sqlite))
        resultado = fuente.leer(capa="wsdcg", datasetCompleto=True)
        assert len(resultado["wsdcg"]) == 2

    def test_leer_dataset_completo(self, params_tuya_tmp, tuya_devices_sqlite):
        fuente = FuenteDatosTuya_SQLITE(str(params_tuya_tmp), str(tuya_devices_sqlite))
        resultado = fuente.leer(datasetCompleto=True)
        assert "wsdcg" in resultado
        assert "kg" in resultado

    def test_exportar_geojson(self, params_tuya_tmp, tuya_devices_sqlite):
        fuente = FuenteDatosTuya_SQLITE(str(params_tuya_tmp), str(tuya_devices_sqlite))
        geojson = fuente.exportar_geojson()
        assert geojson["type"] == "FeatureCollection"
        assert len(geojson["features"]) > 0
        for feat in geojson["features"]:
            assert feat["geometry"]["type"] == "Point"

    def test_exportar_geojson_por_capa(self, params_tuya_tmp, tuya_devices_sqlite):
        fuente = FuenteDatosTuya_SQLITE(str(params_tuya_tmp), str(tuya_devices_sqlite))
        geojson = fuente.exportar_geojson(capa="wsdcg")
        assert len(geojson["features"]) == 2

    def test_exportar_geojson_capa_inexistente(self, params_tuya_tmp, tuya_devices_sqlite):
        fuente = FuenteDatosTuya_SQLITE(str(params_tuya_tmp), str(tuya_devices_sqlite))
        with pytest.raises(Exception, match="No existe la tabla"):
            fuente.exportar_geojson(capa="NO_EXISTE")

    def test_error_init_sin_ruta(self, params_tuya_tmp):
        with pytest.raises(Exception):
            FuenteDatosTuya_SQLITE(str(params_tuya_tmp), None)


# --------------------------------------------------------------------------- #
# Tests: FuenteDatosTuya_OGR (SQLite → OGR)
# --------------------------------------------------------------------------- #
class TestFuenteDatosTuyaOGR:
    def test_init(self, params_tuya_tmp, tuya_devices_sqlite):
        fuente = FuenteDatosTuya_OGR(str(params_tuya_tmp), str(tuya_devices_sqlite))
        assert fuente.ruta_sqlite == str(tuya_devices_sqlite)

    def test_leer_sin_parametros(self, params_tuya_tmp, tuya_devices_sqlite):
        pytest.importorskip("osgeo")
        fuente = FuenteDatosTuya_OGR(str(params_tuya_tmp), str(tuya_devices_sqlite))
        ds = fuente.leer()
        assert ds is not None
        assert ds.GetLayerCount() >= 1
        layer = ds.GetLayerByIndex(0)
        feature = layer.GetNextFeature()
        assert feature is not None

    def test_leer_por_capa(self, params_tuya_tmp, tuya_devices_sqlite):
        pytest.importorskip("osgeo")
        fuente = FuenteDatosTuya_OGR(str(params_tuya_tmp), str(tuya_devices_sqlite))
        ds = fuente.leer(capa="wsdcg")
        assert ds.GetLayerCount() == 1
        layer = ds.GetLayerByIndex(0)
        assert layer.GetName() == "wsdcg"
        assert layer.GetFeatureCount() == 2

    def test_leer_dataset_completo(self, params_tuya_tmp, tuya_devices_sqlite):
        pytest.importorskip("osgeo")
        fuente = FuenteDatosTuya_OGR(str(params_tuya_tmp), str(tuya_devices_sqlite))
        ds = fuente.leer(datasetCompleto=True)
        count = sum(ds.GetLayerByIndex(i).GetFeatureCount() for i in range(ds.GetLayerCount()))
        assert count == 3

    def test_geometria_punto(self, params_tuya_tmp, tuya_devices_sqlite):
        pytest.importorskip("osgeo")
        fuente = FuenteDatosTuya_OGR(str(params_tuya_tmp), str(tuya_devices_sqlite))
        ds = fuente.leer()
        layer = ds.GetLayerByIndex(0)
        feature = layer.GetNextFeature()
        geom = feature.GetGeometryRef()
        assert geom is not None
        assert geom.GetGeometryName() == "POINT"
        x, y = geom.GetX(), geom.GetY()
        assert x != 0 and y != 0

    def test_hereda_exportar(self, params_tuya_tmp, tuya_devices_sqlite):
        from conex.Vector_conex import FuenteDatosVector

        fuente = FuenteDatosTuya_OGR(str(params_tuya_tmp), str(tuya_devices_sqlite))
        assert isinstance(fuente, FuenteDatosVector)
        assert hasattr(fuente, "exportar")
        assert hasattr(fuente, "obtener_capas")
