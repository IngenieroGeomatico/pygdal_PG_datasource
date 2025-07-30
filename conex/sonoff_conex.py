
import os
import sys
import json


class infoSonoff:
    """
    Clase para gestionar la lectura, consulta y exportación de ddatos provenientes de IoT Sonoff.


    """

    def __init__(self, ruta_json_params=None, url=None):
        """
        
        """

        teplateJSON = {
            "router":{
                'IP':'',
                'IP_2':'',
                'SSID':'',
                'pass':'',
                'pass_R':''
            },
            "eWelink":{
                'user_':'',
                'password':"",
                'url':'https://dev.ewelink.cc',
                'user': {
                    'timezone': {}, 
                    'accountLevel': 0, 
                    'countryCode': '', 
                    'email': '', 
                    'apikey': '', 
                    'accountConsult': '', 
                    'appForumEnterHide': '', 
                    'appVersion': '', 
                    'denyRecharge': '', 
                    'ipCountry': ''
                }, 
                'at': '', 
                'rt': '', 
                'region': '', 
                'appid': ''
            }
        }

        if not ruta_json_params:
            dir_base = os.path.dirname(os.path.abspath(__file__))
            ruta_json_conex = os.path.join(dir_base, 'lib_sonoff/params_sonoff.json')
            if not os.path.exists(ruta_json_conex):
                with open(ruta_json_conex, 'w', encoding='utf-8') as f:
                    json.dump(teplateJSON, f, ensure_ascii=False, indent=4)

        if not os.path.exists(ruta_json_params):
            with open(ruta_json_params, 'w', encoding='utf-8') as f:
                json.dump(teplateJSON, f, ensure_ascii=False, indent=4)
            jsonParams = teplateJSON
            print(f'Archivo {ruta_json_params} creado con plantilla por defecto.')
            return 
        else:
            with open(ruta_json_params, 'r', encoding='utf-8') as f:
                try:
                    jsonParams = json.load(f)
                except json.JSONDecodeError:
                    with open(ruta_json_params, 'w', encoding='utf-8') as f:
                        json.dump(teplateJSON, f, ensure_ascii=False, indent=4)
                    print(f'Archivo {ruta_json_params} creado con plantilla por defecto.')
                    return
        print(jsonParams)
        # comprobaciones
        if not jsonParams["eWelink"]["user_"]:
            raise ValueError('El campo "user_" no puede estar vacío en el archivo de parámetros.')
        if not jsonParams["eWelink"]["password"]:
            raise ValueError('El campo "password" no puede estar vacío en el archivo de parámetros.')
        if not jsonParams["eWelink"]["password"]:
            raise ValueError('El campo "password" no puede estar vacío en el archivo de parámetros.')
        
        
        self.ruta_json_params = ruta_json_params
        self.jsonParams = jsonParams


class FuenteDatosSonoff_DualR3:
    """
    Clase para gestionar la lectura, consulta y exportación de ddatos provenientes de IoT Sonoff.


    """

    def __init__(self, ruta_json_conex=None, url=None):
        """
        
        """
        if not ruta_json_conex:
            dir_base = os.path.dirname(os.path.abspath(__file__))
            ruta_json_conex = os.path.join(dir_base, 'lib_sonoff/sonoff.json')
            if not os.path.exists(ruta_json_conex):
                with open(ruta_json_conex, 'w', encoding='utf-8') as f:
                    json.dump({}, f, ensure_ascii=False, indent=4)

        if not os.path.exists(ruta_json_conex):
            with open(ruta_json_conex, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=4)

        self.ruta_json_conex = ruta_json_conex

    def leer(self):
        """
        
        """
        
        return 


    def exportar(self):
        """
        
        """
        
        return 


    def obtener_capas(self):
        """
        
        """
        
        return 


    def ejecutar_sql(self):
        """
        
        """
        
        return 

    
    def MRE_datos(self):
        """
        
        """
        
        return 


    def obtener_atributos(self):
        """
        
        """
        
        return 


    def obtener_nombreCapa(self):
        """
        
        """
        
        return 


    def obtener_indice_capa(self):
        """
        
        """
        
        return 


    def borrar_geometria(self):
        """
        
        """
        
        return 


    def crear_ID(self):
        """
        
        """
        
        return 

    
    def obtener_objeto_porID(self):
        """
        
        """
        
        return 


    def reproyectar_datasource(self):
        """
        
        """
        
        return 


    def añadir_capa(self):
        """
        
        """
        
        return 

