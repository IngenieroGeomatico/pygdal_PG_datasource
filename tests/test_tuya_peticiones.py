"""
Tests unitarios de ``conex.lib_tuyaSmartLife.peticiones_TuyaSmartLife``.

El módulo importa ``tinytuya`` a nivel de módulo. Si no está instalado, se
inyecta un módulo simulado en ``sys.modules`` antes de importar, de modo que los
tests corran siempre. ``tinytuya.deviceScan`` se mockea para no tocar la red.

Estos tests son la regresión de los bugs corregidos:

* ``find_all_devices`` existe (antes se importaba pero no estaba definida).
* ``discover_tuya_by_id_or_ip`` indexa correctamente por id/ip.
"""
import sys
import types

import pytest


@pytest.fixture
def peticiones(monkeypatch):
    """Importa el módulo de peticiones con un tinytuya simulado y controlable."""
    tinytuya_stub = types.ModuleType("tinytuya")

    # deviceScan devuelve un dict indexado por IP, como el real.
    def device_scan(scantime=60):
        return {
            "192.168.1.10": {
                "id": "dev-a",
                "productKey": "pk-a",
                "ver": "3.3",
                "encrypt": True,
                "name": "Enchufe A",
            },
            "192.168.1.11": {
                "id": "dev-b",
                "productKey": "pk-b",
                "ver": "3.1",
                "encrypt": False,
                "name": "Enchufe B",
            },
        }

    tinytuya_stub.deviceScan = MagicMockScan(device_scan)
    monkeypatch.setitem(sys.modules, "tinytuya", tinytuya_stub)

    # Forzar reimport limpio del módulo bajo prueba.
    sys.modules.pop(
        "conex.lib_tuyaSmartLife.peticiones_TuyaSmartLife", None
    )
    import importlib
    modulo = importlib.import_module(
        "conex.lib_tuyaSmartLife.peticiones_TuyaSmartLife"
    )
    importlib.reload(modulo)
    return modulo, tinytuya_stub


class MagicMockScan:
    """Wrapper que registra el último ``scantime`` recibido."""

    def __init__(self, impl):
        self._impl = impl
        self.ultimo_scantime = None
        self.llamadas = 0

    def __call__(self, scantime=60):
        self.ultimo_scantime = scantime
        self.llamadas += 1
        return self._impl(scantime=scantime)


class TestDiscoverTuyaAll:
    def test_indexa_por_id(self, peticiones):
        modulo, _ = peticiones
        resultado = modulo.discover_tuya_all()
        assert set(resultado.keys()) == {"dev-a", "dev-b"}

    def test_mapea_campos(self, peticiones):
        modulo, _ = peticiones
        resultado = modulo.discover_tuya_all()
        a = resultado["dev-a"]
        assert a["ip"] == "192.168.1.10"
        assert a["productKey"] == "pk-a"
        assert a["ver"] == "3.3"
        assert a["encrypt"] is True
        assert a["name"] == "Enchufe A"

    def test_propaga_scantime(self, peticiones):
        modulo, stub = peticiones
        modulo.discover_tuya_all(scan_time=15)
        assert stub.deviceScan.ultimo_scantime == 15


class TestFindAllDevices:
    def test_existe_y_devuelve_dispositivos(self, peticiones):
        """Regresión: find_all_devices se importaba pero no existía."""
        modulo, _ = peticiones
        resultado = modulo.find_all_devices(scan_tcp=True, scantime=120)
        assert set(resultado.keys()) == {"dev-a", "dev-b"}

    def test_propaga_scantime(self, peticiones):
        modulo, stub = peticiones
        modulo.find_all_devices(scantime=99)
        assert stub.deviceScan.ultimo_scantime == 99


class TestDiscoverPorIdOIp:
    def test_por_id(self, peticiones):
        modulo, _ = peticiones
        resultado = modulo.discover_tuya_by_id_or_ip(dev_id="dev-b")
        assert resultado is not None
        assert resultado["ip"] == "192.168.1.11"

    def test_por_ip(self, peticiones):
        modulo, _ = peticiones
        resultado = modulo.discover_tuya_by_id_or_ip(ip="192.168.1.10")
        assert resultado is not None
        assert resultado["productKey"] == "pk-a"

    def test_no_encontrado(self, peticiones):
        modulo, _ = peticiones
        assert modulo.discover_tuya_by_id_or_ip(dev_id="inexistente") is None
