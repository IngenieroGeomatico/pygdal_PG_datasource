import json
import os

import pytest

# Para infoTuyaSmartLife necesita requests (siempre disponible) y tinytuya
pytest.importorskip("requests", reason="requests no instalado")


FILES_DIR = os.path.join(os.path.dirname(__file__), "files")


# --------------------------------------------------------------------------- #
# Tests de bajo nivel: archivo devices_tuyaSmartLife.json
# --------------------------------------------------------------------------- #
class TestDevicesTuyaJSON:
    """Verifica que devices_tuyaSmartLife.json tiene la estructura esperada."""

    @pytest.fixture
    def devices(self):
        ruta = os.path.join(FILES_DIR, "devices_tuyaSmartLife.json")
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)

    def test_archivo_tiene_dispositivos(self, devices):
        assert devices, "El archivo devices_tuyaSmartLife.json está vacío"
        assert len(devices) > 0

    def test_cada_dispositivo_tiene_estructura(self, devices):
        for device_id, device_data in devices.items():
            assert "extra" in device_data
            assert "tuyaSmartLife" in device_data
            assert isinstance(device_id, str)
            assert "long" in device_data["extra"]
            assert "lat" in device_data["extra"]
            tuya_data = device_data["tuyaSmartLife"]
            assert "id" in tuya_data
            assert tuya_data["id"] == device_id
            assert "name" in tuya_data
            assert "category" in tuya_data
            assert "isOnline" in tuya_data

    def test_algun_dispositivo_tiene_coordenadas(self, devices):
        for device_data in devices.values():
            lon = device_data["extra"].get("long")
            lat = device_data["extra"].get("lat")
            if lon and lat and lon != 0 and lat != 0:
                return
        pytest.skip("Ningún dispositivo tiene coordenadas reales (long/lat != 0)")


class TestParamsTuyaJSON:
    """Verifica que params_tuyaSmartLife.json tiene la estructura esperada."""

    @pytest.fixture
    def params(self):
        ruta = os.path.join(FILES_DIR, "params_tuyaSmartLife.json")
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)

    def test_estructura_esperada(self, params):
        assert "tuyaSmartLife" in params
        cfg = params["tuyaSmartLife"]
        assert "AccessID" in cfg.get("user", {})
        assert "AccessSecret" in cfg.get("user", {})

    def test_tiene_router(self, params):
        routers = [k for k in params if k.startswith("router")]
        assert len(routers) > 0


# --------------------------------------------------------------------------- #
# Tests de alto nivel: infoTuyaSmartLife con login mockeado
# --------------------------------------------------------------------------- #
@pytest.fixture
def params_tuya_tmp(tmp_path):
    """Crea un JSON de parámetros Tuya de prueba sin credenciales reales."""
    params = {
        "router": {"IP": "", "SSID": "", "pass": ""},
        "tuyaSmartLife": {
            "user_": "test@example.com",
            "password": "test_password",
            "url": "https://developer.tuya.com/",
            "user": {
                "AccessID": "test_access_id",
                "AccessSecret": "test_access_secret"
            }
        }
    }
    ruta = tmp_path / "params_tuya_test.json"
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(params, f)
    return ruta


@pytest.fixture
def tuya_info(monkeypatch, params_tuya_tmp):
    """Instancia infoTuyaSmartLife con login mockeado (no hace llamadas reales)."""
    fake_auth = {"access_token": "fake_token", "refresh_token": "fake_refresh", "expire_time": 9999}
    monkeypatch.setattr(
        "conex.tuyaSmartLife_conex.infoTuyaSmartLife.login",
        lambda self: fake_auth
    )

    from conex.tuyaSmartLife_conex import infoTuyaSmartLife
    return infoTuyaSmartLife(ruta_json_params=str(params_tuya_tmp))


class TestInfoTuyaConDispositivos:
    """infoTuyaSmartLife.get_devices con readOnlyJSON desde tests/files/."""

    def test_get_devices_read_only(self, tuya_info):
        ruta_devices = os.path.join(FILES_DIR, "devices_tuyaSmartLife.json")
        dispositivos = tuya_info.get_devices(
            ruta_json_devices=ruta_devices,
            readOnlyJSON=True
        )
        assert isinstance(dispositivos, dict)
        assert len(dispositivos) > 0
        for device_id, device_data in dispositivos.items():
            assert "extra" in device_data
            assert "tuyaSmartLife" in device_data
