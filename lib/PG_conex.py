#  Importación de librerías
import json
import psycopg2

"""
PG_conex.py

Módulo para gestionar la conexión y consultas a una base de datos PostgreSQL usando psycopg2.

Clases:
    - ConexPG: Maneja la conexión a PostgreSQL y la ejecución de consultas SQL.

Uso:
    1. Instanciar la clase ConexPG (opcionalmente pasando un diccionario con los parámetros de conexión).
    2. Usar el método conex2PG() para comprobar la conexión o para obtener un objeto de conexión.
    3. Usar el método queryPG() para ejecutar consultas SQL y obtener los resultados.

Ejemplo:
    from lib.PG_conex import ConexPG

    # Instanciar la clase (usando el archivo de configuración por defecto)
    pg = ConexPG()

    # Comprobar la conexión
    pg.conex2PG(check=True)

    # Ejecutar una consulta
    resultado = pg.queryPG("SELECT version();")
    print(resultado)

    # Ejemplo usando el parámetro dataJSONcon
    parametros = {
        'IP': '127.0.0.1',
        'port': '5432',
        'user': 'usuario',
        'pass': 'contraseña',
        'db': 'nombre_basedatos'
    }
    pg2 = ConexPG(dataJSONcon=parametros)
    pg2.conex2PG(check=True)
    resultado2 = pg2.queryPG("SELECT NOW();")
    print(resultado2)
"""
class ConexPG:

    # Se define la función init con los parámetros de construcción de la clase
    def __init__(self,dataJSONcon=None):
        self.conexFile = "./conex/PGconex.json"
        
        if dataJSONcon == None:

            # Opening JSON file
            try:
                f = open(self.conexFile)
            except Exception as e:
                print(e)
                #  Si no existe, se crea el json de configuración
                if "No such file or directory:" in str(e):
                    datajson = {
                        'IP':'',
                        'port':'',
                        'user':'',
                        'pass':'',
                        'db':''
                    }
                    
                    with open(self.conexFile, 'w') as f:
                        json.dump(datajson, f)
                    raise Exception('No existe el archivo de conexión, se crea en el directorio')

            dataJSONcon = json.load(f)
            f.close()
            self.conexJSON = dataJSONcon
        else:
            # Si se pasa un json, se carga directamente
            self.conexJSON = dataJSONcon
    #  Se define un string  para la clase. Esto devolverá la información del objeto BTA instanciado
    def __str__(self):
        return f"archivo de conexión: {self.conexFile}"

    # Función que comprueba si la conexión se hace satisfactoriamente
    def conex2PG(self, check = False):

        db_params = {
            "host": self.conexJSON["IP"],
            "database": self.conexJSON["db"],
            "user": self.conexJSON["user"],
            "password": self.conexJSON["pass"],
            "port": self.conexJSON["port"],
        }

        try:
            # Establishing a connection to the database
            connection = psycopg2.connect(**db_params)
            # Creating a cursor object to interact with the database
            cursor = connection.cursor()
            # Performing database operations here...

        except (Exception, psycopg2.Error) as error:
            print(f"Error connecting to the database: {error}")
            raise Exception(f"Error connecting to the database: {error}")

        finally:
            if connection:
                if check == True:
                    cursor.close()
                    connection.close()
                    print('')
                    print('--------------------------------')
                    print("[v]  Database connection opened and closed.")
                    print('--------------------------------')
                    print('')
                    return "[v]  Database connection opened and closed."
                else:
                    return  connection

    # Función para mandar las sentencias SQL
    def queryPG(self,query):

        # Se realiza la conexión para almacenar el contenido de las tablas en objetos python
        connection = self.conex2PG(self)
        cursor = connection.cursor()

        # Ejecuta la sentencia SQL
        cursor.execute(query)
        returnQuery = cursor.fetchall()
        connection.commit()
        cursor.close()
        connection.close()

        return returnQuery

# Ejemplo de uso:
#
# from lib.PG_conex import ConexPG
#
# # Instanciar la clase (usando el archivo de configuración por defecto)
# pg = ConexPG()
#
# # Comprobar la conexión
# pg.conex2PG(check=True)
#
# # Ejecutar una consulta
# resultado = pg.queryPG("SELECT version();")
# print(resultado)
#
# # Ejemplo usando el parámetro dataJSONcon
# parametros = {
#     'IP': '127.0.0.1',
#     'port': '5432',
#     'user': 'usuario',
#     'pass': 'contraseña',
#     'db': 'nombre_basedatos'
# }
# pg2 = ConexPG(dataJSONcon=parametros)
# pg2.conex2PG(check=True)
# resultado2 = pg2.queryPG("SELECT NOW();")
# print(resultado2)