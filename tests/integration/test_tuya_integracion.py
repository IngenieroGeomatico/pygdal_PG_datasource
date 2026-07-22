"""
Tests de INTEGRACIÓN del conector Tuya (sustituyen a test/puntero_tuyaSmartLife.py).

Requieren credenciales Tuya Cloud reales. El JSON de parámetros se indica con:

    TUYA_PARAMS_JSON=/ruta/a/params_tuyaSmartLife.json

El JSON debe contener tuyaSmartLife.user_, password y user.AccessID/AccessSecret
válidos. Se saltan si falta la variable, el archivo o tinytuya.

Ejecutar:  pytest -m integration tests/integration/test_tuya_integracion.py
"""
import pytest

pytestmark = pytest.mark.integration

pytest.importorskip("tinytuya", reason="tinytuya no instalado")


def test_login_tuya(tuya_params_path):
    from conex.tuyaSmartLife_conex import infoTuyaSmartLife

    info = infoTuyaSmartLife(ruta_json_params=tuya_params_path)
    assert info.auth is not None
    assert "access_token" in info.auth


def test_refresh_token(tuya_params_path):
    from conex.tuyaSmartLife_conex import infoTuyaSmartLife

    info = infoTuyaSmartLife(ruta_json_params=tuya_params_path)
    auth = info.refreshAT()
    assert auth is not None
    assert "access_token" in auth
