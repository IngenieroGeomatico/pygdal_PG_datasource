"""
Configuración compartida de pytest para pygdal_PG_datasource.

Añade la raíz del repositorio al ``sys.path`` para poder importar el paquete
``conex`` sin necesidad de instalar la librería.

Proporciona ``FILES_DIR`` (ruta a ``tests/files/``) y el fixture ``files_dir``
para que los tests unitarios puedan leer y escribir datos de prueba sin rutas
hardcodeadas.
"""
import os
import sys

import pytest

RAIZ_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if RAIZ_REPO not in sys.path:
    sys.path.insert(0, RAIZ_REPO)

FILES_DIR = os.path.join(os.path.dirname(__file__), "files")


@pytest.fixture
def files_dir():
    return FILES_DIR
