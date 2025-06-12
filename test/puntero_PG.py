import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.PG_conex import ConexPG

# Ejemplo usando el parámetro dataJSONcon
parametros = {
    'IP': '172.17.0.1',
    'port': '5432',
    'user': 'usuario',
    'pass': 'pass',
    'db': 'postgis'
}
pg2 = ConexPG(dataJSONcon=parametros)
pg2.conex2PG(check=True)
print("----")
print("DateTime ahora:")
resultado1 = pg2.queryPG("SELECT NOW();")
print(resultado1)
print("----")

print("----")
print("Versión de PG y PGIS:")
resultado2 = pg2.queryPG("SELECT version(), PostGIS_Version();")
print(resultado2)
print("----")

print("----")
print("Área de influencia:")
resultado3 = pg2.queryPG("SELECT  ST_AsText(ST_Buffer(ST_SetSRID(ST_MakePoint(-3, 40), 4326), 0.01)) AS wkt_buffer;")
print(resultado3)
print("----")





