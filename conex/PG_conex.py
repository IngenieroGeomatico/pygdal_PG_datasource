#  Importación de librerías
import json
import logging
import psycopg2

logger = logging.getLogger(__name__)

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
                logger.error(e)
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
    def conex2PG(self, check=False):
        """
        Establece la conexión con PostgreSQL.

        Parámetros
        ----------
        check : bool, opcional
            Si es True, abre y cierra la conexión (modo verificación) y devuelve
            un mensaje de confirmación. Si es False (por defecto), devuelve el
            objeto ``connection`` abierto para su uso posterior.

        Retorna
        -------
        psycopg2.extensions.connection o str
            Objeto de conexión (check=False) o mensaje de confirmación (check=True).
        """

        db_params = {
            "host": self.conexJSON["IP"],
            "database": self.conexJSON["db"],
            "user": self.conexJSON["user"],
            "password": self.conexJSON["pass"],
            "port": self.conexJSON["port"],
        }

        try:
            # Estableciendo conexión a la base de datos
            connection = psycopg2.connect(**db_params)
        except (Exception, psycopg2.Error) as error:
            logger.error(f"Error al conectar a la base de datos: {error}")
            raise Exception(f"Error al conectar a la base de datos: {error}")

        if check:
            # Modo verificación: comprobamos que se puede abrir un cursor y cerramos.
            connection.close()
            logger.info("[v]  Conexión a la base de datos abierta y cerrada.")
            return "[v]  Conexión a la base de datos abierta y cerrada."

        return connection

    # Función para mandar las sentencias SQL
    def queryPG(self, query):

        # Se realiza la conexión para almacenar el contenido de las tablas en objetos python
        connection = self.conex2PG()
        try:
            cursor = connection.cursor()
            # Ejecuta la sentencia SQL
            cursor.execute(query)
            returnQuery = cursor.fetchall()
            connection.commit()
            cursor.close()
        finally:
            connection.close()

        return returnQuery

