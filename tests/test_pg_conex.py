"""
Tests unitarios de ``conex.PG_conex.ConexPG``.

Se mockea ``psycopg2.connect`` para probar la lógica de conexión y consulta sin
necesidad de una base de datos PostgreSQL real. Estos tests son la regresión de
los bugs corregidos:

* ``queryPG`` ya no llama a ``conex2PG(self)`` (que rompía con AttributeError).
* ``conex2PG(check=True)`` abre y cierra la conexión sin dejar recursos abiertos.
* ``queryPG`` cierra siempre la conexión (incluso ante errores).
"""
from unittest.mock import MagicMock

import pytest

from conex.PG_conex import ConexPG


PARAMS = {
    "IP": "127.0.0.1",
    "port": "5432",
    "user": "u",
    "pass": "p",
    "db": "postgis",
}


@pytest.fixture
def conexion_mock(monkeypatch):
    """Parchea psycopg2.connect y devuelve (ConexPG, connection_mock, cursor_mock)."""
    cursor = MagicMock(name="cursor")
    connection = MagicMock(name="connection")
    connection.cursor.return_value = cursor

    connect = MagicMock(name="connect", return_value=connection)
    # El módulo importa psycopg2 dentro de conex.PG_conex
    import conex.PG_conex as pg_mod
    monkeypatch.setattr(pg_mod.psycopg2, "connect", connect)

    pg = ConexPG(dataJSONcon=dict(PARAMS))
    return pg, connection, cursor, connect


class TestConex2PG:
    def test_check_true_abre_y_cierra(self, conexion_mock):
        pg, connection, cursor, connect = conexion_mock
        resultado = pg.conex2PG(check=True)

        connect.assert_called_once()
        connection.close.assert_called_once()
        assert isinstance(resultado, str)
        assert "closed" in resultado.lower()

    def test_check_false_devuelve_conexion_abierta(self, conexion_mock):
        pg, connection, cursor, connect = conexion_mock
        resultado = pg.conex2PG(check=False)

        assert resultado is connection
        connection.close.assert_not_called()

    def test_pasa_parametros_correctos(self, conexion_mock):
        pg, connection, cursor, connect = conexion_mock
        pg.conex2PG(check=True)

        _, kwargs = connect.call_args
        assert kwargs["host"] == PARAMS["IP"]
        assert kwargs["database"] == PARAMS["db"]
        assert kwargs["user"] == PARAMS["user"]
        assert kwargs["password"] == PARAMS["pass"]
        assert kwargs["port"] == PARAMS["port"]

    def test_error_de_conexion_se_propaga(self, conexion_mock, monkeypatch):
        pg, connection, cursor, connect = conexion_mock
        connect.side_effect = Exception("boom")
        with pytest.raises(Exception):
            pg.conex2PG(check=True)


class TestQueryPG:
    def test_query_ejecuta_y_devuelve_resultados(self, conexion_mock):
        pg, connection, cursor, connect = conexion_mock
        cursor.fetchall.return_value = [("2024-01-01",)]

        resultado = pg.queryPG("SELECT NOW();")

        cursor.execute.assert_called_once_with("SELECT NOW();")
        cursor.fetchall.assert_called_once()
        connection.commit.assert_called_once()
        assert resultado == [("2024-01-01",)]

    def test_query_cierra_conexion(self, conexion_mock):
        pg, connection, cursor, connect = conexion_mock
        cursor.fetchall.return_value = []

        pg.queryPG("SELECT 1;")

        cursor.close.assert_called_once()
        connection.close.assert_called_once()

    def test_query_cierra_conexion_ante_error(self, conexion_mock):
        """Regresión: la conexión debe cerrarse aunque execute lance."""
        pg, connection, cursor, connect = conexion_mock
        cursor.execute.side_effect = Exception("SQL error")

        with pytest.raises(Exception):
            pg.queryPG("SELECT bad;")

        connection.close.assert_called_once()

    def test_query_no_pasa_self_a_conex2PG(self, conexion_mock):
        """Regresión del bug original: queryPG llamaba a conex2PG(self)."""
        pg, connection, cursor, connect = conexion_mock
        cursor.fetchall.return_value = [(1,)]

        # No debe lanzar AttributeError por tratar un string como conexión.
        assert pg.queryPG("SELECT 1;") == [(1,)]
