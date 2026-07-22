"""
Tests de INTEGRACIÓN de los conectores Sonoff (sustituyen a test/puntero_Sonoff.py).

Requieren credenciales eWeLink reales y (para el estado) dispositivos físicos en
la red local. El JSON de parámetros se indica con:

    EWELINK_PARAMS_JSON=/ruta/a/params_sonoff.json

El JSON debe contener eWeLink.user_, password y countryCode válidos. Se saltan
si falta la variable, el archivo, GDAL o las dependencias IoT (Crypto/zeroconf).

Ejecutar:  pytest -m integration tests/integration/test_sonoff_integracion.py
"""
import pytest

pytestmark = pytest.mark.integration

# Dependencias opcionales necesarias para los conectores Sonoff.
pytest.importorskip("Crypto", reason="pycryptodome no instalado")
pytest.importorskip("zeroconf", reason="zeroconf no instalado")


def test_login_ewelink(ewelink_params_path):
    from conex.sonoff_conex import infoSonoff

    info = infoSonoff(ruta_json_params=ewelink_params_path)
    assert info.auth is not None
    assert "at" in info.auth


def test_get_devices(ewelink_params_path, tmp_path):
    from conex.sonoff_conex import infoSonoff

    info = infoSonoff(ruta_json_params=ewelink_params_path)
    ruta_devices = str(tmp_path / "devices_sonoff.json")
    dispositivos = info.get_devices(auth=info.auth, ruta_json_devices=ruta_devices)
    assert isinstance(dispositivos, dict)
