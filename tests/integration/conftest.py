"""
Infraestructura para los tests de INTEGRACIÓN.

Estos tests ejercitan recursos externos reales (servicios web WFS/WMS, CDNs,
PostgreSQL, dispositivos IoT). Sustituyen a los antiguos scripts manuales
``test/puntero_*.py``, pero con aserciones y con *skip* automático cuando el
recurso no está disponible, de modo que:

* ``pytest``            -> los salta todos (marca ``integration`` desactivada).
* ``pytest -m integration`` -> ejecuta solo los que tengan su recurso disponible.

Ningún test lleva credenciales embebidas: se leen de variables de entorno.
"""
import os

import pytest


# --------------------------------------------------------------------------- #
# Configuración PostgreSQL (por variables de entorno)
# --------------------------------------------------------------------------- #
def config_pg_desde_entorno():
    """
    Lee la configuración de PostgreSQL desde variables de entorno.

    Variables: PG_TEST_HOST, PG_TEST_PORT, PG_TEST_USER, PG_TEST_PASS, PG_TEST_DB.
    Devuelve el dict en el formato que espera ``ConexPG`` o ``None`` si falta
    alguna variable obligatoria.
    """
    host = os.environ.get("PG_TEST_HOST")
    user = os.environ.get("PG_TEST_USER")
    db = os.environ.get("PG_TEST_DB")
    if not (host and user and db):
        return None
    return {
        "IP": host,
        "port": os.environ.get("PG_TEST_PORT", "5432"),
        "user": user,
        "pass": os.environ.get("PG_TEST_PASS", ""),
        "db": db,
    }


@pytest.fixture
def pg_config():
    cfg = config_pg_desde_entorno()
    if cfg is None:
        pytest.skip("Faltan variables PG_TEST_HOST/USER/DB para el test de PostgreSQL")
    return cfg


# --------------------------------------------------------------------------- #
# Configuración eWeLink / Tuya (por variables de entorno)
# --------------------------------------------------------------------------- #
@pytest.fixture
def ewelink_params_path():
    """Ruta a un JSON de parámetros eWeLink válido (EWELINK_PARAMS_JSON)."""
    ruta = os.environ.get("EWELINK_PARAMS_JSON")
    if not ruta or not os.path.exists(ruta):
        pytest.skip("Falta EWELINK_PARAMS_JSON apuntando a un JSON de parámetros válido")
    return ruta


@pytest.fixture
def tuya_params_path():
    """Ruta a un JSON de parámetros Tuya válido (TUYA_PARAMS_JSON)."""
    ruta = os.environ.get("TUYA_PARAMS_JSON")
    if not ruta or not os.path.exists(ruta):
        pytest.skip("Falta TUYA_PARAMS_JSON apuntando a un JSON de parámetros válido")
    return ruta
