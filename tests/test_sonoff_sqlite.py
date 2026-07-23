import json
import os
import sqlite3

import pytest

# sonoff_conex maneja internamente las dependencias opcionales (zeroconf, Crypto)
# con imports diferidos. No es necesario importorskip aquí.
from conex.sonoff_conex import infoSonoff  # noqa: E402


FILES_DIR = os.path.join(os.path.dirname(__file__), "files")


# --------------------------------------------------------------------------- #
# Tests de bajo nivel: acceso directo a la SQLite con sqlite3
# --------------------------------------------------------------------------- #
class TestSQLiteDirecto:
    """Verifica que devices_sonoff.sqlite es válido y tiene la estructura esperada."""

    @pytest.fixture
    def conn(self):
        ruta = os.path.join(FILES_DIR, "devices_sonoff.sqlite")
        conn = sqlite3.connect(ruta)
        yield conn
        conn.close()

    def test_tablas_existentes(self, conn):
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tablas = {row[0] for row in cursor.fetchall()}
        assert tablas, "No hay tablas en la base de datos"
        # Debería contener tipos de dispositivos Sonoff (ej: MINIR4, DUALR3)
        assert "MINIR4" in tablas
        assert "DUALR3" in tablas

    def test_columnas_esperadas(self, conn):
        cursor = conn.execute("PRAGMA table_info(MINIR4)")
        cols = {row[1] for row in cursor.fetchall()}
        assert "id" in cols
        assert "extra" in cols
        assert "ewelinkData" in cols
        assert "state" in cols

    def test_datos_no_vacios(self, conn):
        for tabla in ["MINIR4", "DUALR3"]:
            cursor = conn.execute(f"SELECT count(*) FROM {tabla}")
            count = cursor.fetchone()[0]
            assert count > 0, f"La tabla {tabla} está vacía"

    def test_extra_contiene_coordenadas(self, conn):
        cursor = conn.execute("SELECT extra FROM MINIR4 LIMIT 1")
        extra_raw = cursor.fetchone()[0]
        extra = json.loads(extra_raw)
        assert "long" in extra
        assert "lat" in extra
        assert isinstance(extra["long"], float)
        assert isinstance(extra["lat"], float)

    def test_ewelinkData_contiene_devicekey(self, conn):
        cursor = conn.execute("SELECT ewelinkData FROM DUALR3 LIMIT 1")
        raw = cursor.fetchone()[0]
        data = json.loads(raw)
        assert "devicekey" in data
        assert "deviceid" in data
        assert "productModel" in data


# --------------------------------------------------------------------------- #
# Tests de alto nivel: infoSonoff con login mockeado
# --------------------------------------------------------------------------- #
@pytest.fixture
def params_sonoff_tmp(tmp_path):
    """Crea un JSON de parámetros Sonoff de prueba en un directorio temporal."""
    params = {
        "router": {
            "IP": "",
            "IP_2": "",
            "SSID": "",
            "pass": "",
            "pass_R": ""
        },
        "eWelink": {
            "user_": "test@example.com",
            "password": "test_password",
            "countryCode": "+34",
            "url": "https://dev.ewelink.cc",
            "user": {}
        }
    }
    ruta = tmp_path / "params_sonoff_test.json"
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(params, f)
    return ruta


@pytest.fixture
def sonoff_info(monkeypatch, params_sonoff_tmp):
    """Instancia infoSonoff con login mockeado (no hace llamadas reales)."""
    fake_auth = {"at": "fake_at_token", "rt": "fake_rt_token", "appid": "fake_appid"}
    monkeypatch.setattr("conex.sonoff_conex.infoSonoff.login", lambda self, app=2: fake_auth)

    return infoSonoff(ruta_json_params=str(params_sonoff_tmp))


class TestInfoSonoffConSQLite:
    """infoSonoff con el SQLite real y login mockeado."""

    @pytest.fixture
    def ruta_sqlite(self):
        return os.path.join(FILES_DIR, "devices_sonoff.sqlite")

    def test_obtener_tipos_sqlite(self, sonoff_info, ruta_sqlite):
        sonoff_info.ruta_SQLite_devices = ruta_sqlite
        tipos = sonoff_info.obtener_tipos_sqlite()
        assert "MINIR4" in tipos
        assert "DUALR3" in tipos

    def test_dividir_por_tipo_sqlite(self, sonoff_info, ruta_sqlite):
        sonoff_info.ruta_SQLite_devices = ruta_sqlite
        por_tipo = sonoff_info.dividir_por_tipo_sqlite()
        assert "MINIR4" in por_tipo
        assert "DUALR3" in por_tipo
        assert len(por_tipo["MINIR4"]) >= 2
        assert len(por_tipo["DUALR3"]) >= 2
        # Verificar que los registros tienen los campos esperados
        primer_registro = por_tipo["MINIR4"][0]
        assert "id" in primer_registro
        assert "extra" in primer_registro
        assert "ewelinkData" in primer_registro
        assert "state" in primer_registro

    def test_dividir_por_tipo_sqlite_filtrado(self, sonoff_info, ruta_sqlite):
        sonoff_info.ruta_SQLite_devices = ruta_sqlite
        por_tipo = sonoff_info.dividir_por_tipo_sqlite(tipo="DUALR3")
        assert "DUALR3" in por_tipo
        assert "MINIR4" not in por_tipo
