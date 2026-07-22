"""
Tests de INTEGRACIÓN de ``ConexPG`` (sustituyen a test/puntero_PG.py).

Requieren un PostgreSQL/PostGIS real. La configuración se toma de variables de
entorno (ver conftest.config_pg_desde_entorno):

    PG_TEST_HOST, PG_TEST_PORT, PG_TEST_USER, PG_TEST_PASS, PG_TEST_DB

Se saltan si faltan esas variables.

Ejecutar:  pytest -m integration tests/integration/test_pg_integracion.py
"""
import pytest

pytestmark = pytest.mark.integration


def test_conexion_check(pg_config):
    from conex.PG_conex import ConexPG

    pg = ConexPG(dataJSONcon=pg_config)
    resultado = pg.conex2PG(check=True)
    assert "closed" in resultado.lower()


def test_query_now(pg_config):
    from conex.PG_conex import ConexPG

    pg = ConexPG(dataJSONcon=pg_config)
    resultado = pg.queryPG("SELECT NOW();")
    assert len(resultado) == 1
    assert resultado[0][0] is not None


def test_query_version(pg_config):
    from conex.PG_conex import ConexPG

    pg = ConexPG(dataJSONcon=pg_config)
    resultado = pg.queryPG("SELECT version();")
    assert "PostgreSQL" in resultado[0][0]


@pytest.mark.skipif(True, reason="Requiere extensión PostGIS; habilitar manualmente")
def test_query_postgis_buffer(pg_config):
    from conex.PG_conex import ConexPG

    pg = ConexPG(dataJSONcon=pg_config)
    resultado = pg.queryPG(
        "SELECT ST_AsText(ST_Buffer(ST_SetSRID(ST_MakePoint(-3, 40), 4326), 0.01));"
    )
    assert resultado[0][0].upper().startswith("POLYGON")
