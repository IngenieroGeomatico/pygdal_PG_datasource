"""
Configuración compartida de pytest para pygdal_PG_datasource.

Añade la raíz del repositorio al ``sys.path`` para poder importar el paquete
``conex`` sin necesidad de instalar la librería.
"""
import os
import sys

RAIZ_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if RAIZ_REPO not in sys.path:
    sys.path.insert(0, RAIZ_REPO)
