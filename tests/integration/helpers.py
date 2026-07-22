"""
Helpers de disponibilidad y skip para los tests de integración.

Se mantienen aquí (módulo importable normal) en vez de en ``conftest.py`` para
poder importarlos de forma explícita desde los tests sin depender del mecanismo
especial de descubrimiento de conftest de pytest.
"""
import socket

import pytest


def hay_conectividad(host="1.1.1.1", puerto=443, timeout=3.0):
    """Devuelve True si hay salida a Internet (conexión TCP de prueba)."""
    try:
        with socket.create_connection((host, puerto), timeout=timeout):
            return True
    except OSError:
        return False


def host_alcanzable(host, puerto, timeout=3.0):
    """True si se puede abrir una conexión TCP al host:puerto indicado."""
    try:
        with socket.create_connection((host, puerto), timeout=timeout):
            return True
    except OSError:
        return False


def gdal_disponible():
    try:
        import osgeo  # noqa: F401
        return True
    except Exception:
        return False


# Marcadores de skip reutilizables.
requiere_red = pytest.mark.skipif(
    not hay_conectividad(),
    reason="Sin conectividad a Internet",
)

requiere_gdal = pytest.mark.skipif(
    not gdal_disponible(),
    reason="GDAL/OGR (osgeo) no instalado",
)
