"""
Tests unitarios de ``conex.lib_sonoff.cripto_sonoff``.

Requieren ``pycryptodome`` (paquete ``Crypto``). Si no está instalado, todos los
tests de este módulo se saltan limpiamente.
"""
import pytest

# Salta todo el módulo si pycryptodome no está disponible.
pytest.importorskip("Crypto", reason="pycryptodome no instalado")

from conex.lib_sonoff import cripto_sonoff  # noqa: E402


class TestPadding:
    def test_pad_unpad_round_trip(self):
        for texto in [b"", b"a", b"1234567890123456", b"bloque parcial"]:
            padded = cripto_sonoff.pad(texto, 16)
            assert len(padded) % 16 == 0
            assert cripto_sonoff.unpad(padded, 16) == texto

    def test_pad_bloque_completo_anade_bloque(self):
        # PKCS#7: si el dato ya es múltiplo, se añade un bloque entero.
        datos = b"0123456789ABCDEF"  # 16 bytes
        padded = cripto_sonoff.pad(datos, 16)
        assert len(padded) == 32
        assert cripto_sonoff.unpad(padded, 16) == datos


class TestEncryptDecrypt:
    def test_round_trip(self):
        devicekey = "clave-de-dispositivo"
        payload = {"data": {"switch": "on", "power": 42}}

        cifrado = cripto_sonoff.encrypt(dict(payload), devicekey)
        assert cifrado["encrypt"] is True
        assert "iv" in cifrado
        assert isinstance(cifrado["data"], str)  # base64

        descifrado = cripto_sonoff.decrypt(cifrado, devicekey)
        assert descifrado["data"] == payload["data"]

    def test_iv_aleatorio_cambia_texto_cifrado(self):
        devicekey = "k"
        payload = {"data": {"x": 1}}
        c1 = cripto_sonoff.encrypt(dict(payload), devicekey)
        c2 = cripto_sonoff.encrypt(dict(payload), devicekey)
        # Con IV aleatorio, dos cifrados del mismo dato difieren.
        assert c1["data"] != c2["data"] or c1["iv"] != c2["iv"]
