
# Python
import os
import re
import sys
import json
import hmac
import copy
import base64
import sqlite3
import hashlib
import requests
import datetime

try:
    from osgeo import ogr, osr, gdal
except:
    sys.exit('ERROR: cannot find GDAL/OGR modules')

from .lib_sonoff.peticiones_sonoff import mDNS_todos, mDNS
from .lib_sonoff.cripto_sonoff import decrypt

from .Vector_conex import FuenteDatosVector

class infoSonoff:
    """
    Clase para gestionar la lectura, consulta y exportación de ddatos provenientes de IoT Sonoff.
    """

    def __init__(self, ruta_json_params=None):
        """
        
        """
        templateJSON = {
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
                "countryCode": "",
                'url':'https://dev.ewelink.cc',
                'user': {}, 
            }
        }

        # Constantes
        self.region = {
            'MainlandChina': 'https://cn-apia.coolkit.cn',
            'Asia': 'https://as-apia.coolkit.cc',
            'Americas': 'https://us-apia.coolkit.cc',
            'Europe': 'https://eu-apia.coolkit.cc',
        }

        self.APP = [
            ("oeVkj2lYFGnJu5XUtWisfW4utiN4u9Mq", "6Nz4n0xA8s8qdxQf2GqurZj2Fs55FUvM"),
            ("KOBxGJna5qkk3JLXw3LHLX3wSNiPjAVi", "4v0sv6X5IM2ASIBiNDj6kGmSfxo40w7n"),
            ("4s1FXKC9FaGfoqXhmXSJneb3qcm1gOak", "oKvCM06gvwkRbfetd6qWRrbC3rFrbIpV"),
            ("R8Oq3y0eSZSYdKccHlrQzT1ACCOUT9Gv", "1ve5Qk9GXfUhKAn1svnKwpAlxXkMarru"),
        ]

        self.ruta_json_params = None
        self.jsonParams = None
        self.auth = None
        self.ruta_json_devices = None
        self.jsonDevices = None
        self.ruta_SQLite_devices = None

        if not ruta_json_params:
            dir_base = os.path.dirname(os.path.abspath(__file__))
            ruta_json_conex = os.path.join(dir_base, 'lib_sonoff/params_sonoff.json')
            if not os.path.exists(ruta_json_conex):
                with open(ruta_json_conex, 'w', encoding='utf-8') as f:
                    json.dump(templateJSON, f, ensure_ascii=False, indent=4)

        if not os.path.exists(ruta_json_params):
            with open(ruta_json_params, 'w', encoding='utf-8') as f:
                json.dump(templateJSON, f, ensure_ascii=False, indent=4)
            jsonParams = templateJSON
            print(f'Archivo {ruta_json_params} creado con plantilla por defecto.')
        
        else:
            with open(ruta_json_params, 'r', encoding='utf-8') as f:
                try:
                    jsonParams = json.load(f)
                except json.JSONDecodeError:
                    with open(ruta_json_params, 'w', encoding='utf-8') as f:
                        json.dump(templateJSON, f, ensure_ascii=False, indent=4)
                    print(f'Archivo {ruta_json_params} creado con plantilla por defecto.')
                    return
                
        self.ruta_json_params = ruta_json_params
        self.jsonParams = jsonParams

        # comprobaciones
        if not jsonParams["eWelink"]["user_"]:
            raise ValueError('El campo "user_" no puede estar vacío en el archivo de parámetros.')
        if not jsonParams["eWelink"]["password"]:
            raise ValueError('El campo "password" no puede estar vacío en el archivo de parámetros.')
        if not jsonParams["eWelink"]["password"]:
            raise ValueError('El campo "password" no puede estar vacío en el archivo de parámetros.')
        if not jsonParams["eWelink"]["countryCode"]:
            raise ValueError('El campo "countryCode" no puede estar vacío en el archivo de parámetros.')
        
        jsonParams["eWelink"].update(self.login())
        with open(ruta_json_params, 'w', encoding='utf-8') as f:
            json.dump(jsonParams, f, ensure_ascii=False, indent=4)

        self.jsonParams = jsonParams
        self.auth ={'at': self.jsonParams["eWelink"]["at"] }

    # Funciones
    def makeSign(self, key, message):
        """
        Generate a signature for a message using a key.

        Parameters
        ----------
        key : str
            The key used to generate the signature.
        message : str
            The message to be signed.

        Returns
        -------
        str
            The base64 encoded signature.
        """
        j = hmac.new(key.encode(), message.encode(), digestmod=hashlib.sha256)
        return (base64.b64encode(j.digest())).decode()

    def login(self, app=2):
            password = self.jsonParams["eWelink"]["password"]
            username = self.jsonParams["eWelink"]["user_"]
            countryCode = self.jsonParams["eWelink"]["countryCode"]
            # https://coolkit-technologies.github.io/eWeLink-API/#/en/DeveloperGuideV2
            payload = {
                "password": password,
                "countryCode":countryCode,
            }
            if "@" in username:
                payload["email"] = username

            appid, appsecret = self.APP[app]

            # ensure POST payload and Sign payload will be same
            data = json.dumps(payload).encode()
            hex_dig = hmac.new(appsecret.encode(), data, hashlib.sha256).digest()

            headers = {
                "Authorization": "Sign " + base64.b64encode(hex_dig).decode(),
                "Content-Type": "application/json",
                "X-CK-Appid": appid,
            }
            r = requests.post(
                self.region['Europe'] + "/v2/user/login", data=data, headers=headers, timeout=30
            )
            resp = r.json()

            # wrong default region
            if resp["error"] == 10004:
                self.region['Europe'] = resp["data"]["region"]
                r = requests.post(
                    self.region['Europe']  + "/v2/user/login", data=data, headers=headers, timeout=30
                )
                resp = r.json()

            if resp["error"] != 0:
                raise Exception(resp)

            auth = resp["data"]
            auth["appid"] = appid

            return auth

    def refreshAT(self, auth: dict, app=2):
        
        def headers() -> dict:
            return {
                "Authorization": "Bearer " + auth["at"],
                "X-CK-Appid": appid,
                "Content-Type": "application/json"
            }

        appid, appsecret = APP[app]

        r = requests.post(
            self.region['Europe']+ "/v2/user/refresh",
            headers=headers(),
            timeout=30,
            params={"rt": auth["rt"]},
        )
        resp = r.json()
        if resp["error"] != 0:
            raise Exception(resp["msg"])

        return resp

    def logout(self,auth: dict, app=2):

        def headers() -> dict:
            return {
                "Authorization": "Bearer " + auth["at"],
                "X-CK-Appid": appid
                }

        appid, appsecret = APP[app]

        r = requests.delete(
            self.region['Europe']+ "/v2/user/logout",
            headers=headers(),
            timeout=30
        )
        resp = r.json()
        if resp["error"] != 0:
            raise Exception(resp["msg"])

        return resp

    def get_devices(self, auth: dict, ruta_json_devices = None, readOnlyJSON = False):

        if readOnlyJSON:
            with open(ruta_json_devices, 'r', encoding='utf-8') as f:
                try:
                    jsonDevices = json.load(f)
                    self.ruta_json_devices = ruta_json_devices
                    self.jsonDevices = jsonDevices
                    return jsonDevices
                except json.JSONDecodeError:
                    pass
                    

        def headers() -> dict:
            return {"Authorization": "Bearer " + auth["at"]}

        devices = []
        r = requests.get(
            self.region['Europe']+ "/v2/device/thing",
            headers=headers(),
            timeout=30,
            params={"num": 0},
        )
        resp = r.json()
        if resp["error"] != 0:
            raise Exception(resp["msg"])
        # item type: 1 - user device, 2 - shared device, 3 - user group,
        # 5 - share device (home)
        devices += [
            i["itemData"]
            for i in resp["data"]["thingList"]
            if i["itemType"] != 3  # skip groups
        ]

        templateJSON = {}
        for device in devices:

            templateJSONDevice = {
                        'extra':{},
                        'ewelinkData':{}
            }
            templateJSONDevice['ewelinkData'] = device
            templateJSON[device["deviceid"]] = templateJSONDevice

        if not ruta_json_devices:
            dir_base = os.path.dirname(os.path.abspath(__file__))
            ruta_json_devices = os.path.join(dir_base, 'lib_sonoff/devices_sonoff.json')
            if not os.path.exists(ruta_json_devices):
                with open(ruta_json_devices, 'w', encoding='utf-8') as f:
                    json.dump(templateJSON, f, ensure_ascii=False, indent=4)
                jsonDevices = templateJSON
                print(f'Archivo {ruta_json_devices} creado con plantilla por defecto.')

        if not os.path.exists(ruta_json_devices):
            with open(ruta_json_devices, 'w', encoding='utf-8') as f:
                json.dump(templateJSON, f, ensure_ascii=False, indent=4)
            jsonDevices = templateJSON
            print(f'Archivo {ruta_json_devices} creado con plantilla por defecto.')

        else:
            with open(ruta_json_devices, 'w', encoding='utf-8') as f:
                json.dump(templateJSON, f, ensure_ascii=False, indent=4)
            jsonDevices = templateJSON
            print(f'Archivo {ruta_json_devices} creado con plantilla por defecto.')
                
        self.ruta_json_devices = ruta_json_devices
        self.jsonDevices = jsonDevices
        return jsonDevices

    def get_state_devices(self, idDevice=None):
        if not self.jsonDevices:
            raise Exception('Se tiene que lanzar primero get_devices() para obtener los dispositivos')
        
        # Procesa todos los dispositivos
        if not idDevice:
            datas = mDNS_todos(self.jsonDevices)
            # Preprocesa deviceid -> keyDevice y device
            device_map = {v['ewelinkData']['deviceid']: (k, v['ewelinkData']['devicekey']) for k, v in self.jsonDevices.items()}
            for id, data in datas.items():
                # Unifica los datos
                if 'data1' in data and 'data2' in data and 'data3' in data:
                    data['data'] = data['data1'] + data['data2'] + data['data3']
                    for key in ['data1', 'data2', 'data3']:
                        data.pop(key)
                elif 'data1' in data and 'data2' in data:
                    data['data'] = data['data1'] + data['data2']
                    for key in ['data1', 'data2']:
                        data.pop(key)
                elif 'data1' in data:
                    data['data'] = data['data1']
                    data.pop('data1')
                
                # Busca device y keyDevice
                if id in device_map:
                    device, keyDevice = device_map[id]
                    if 'data' in data:
                        data = decrypt(payload=data, devicekey=keyDevice)
                    self.jsonDevices[device]['state'] = data
                    self.jsonDevices[device]['extra']['datetime'] = datetime.datetime.now().isoformat()
                else:
                    print(f"Dispositivo {id} no encontrado en jsonDevices.")
            
            # Escribe solo una vez al final
            with open(self.ruta_json_devices, 'w', encoding='utf-8') as f:
                json.dump(self.jsonDevices, f, ensure_ascii=False, indent=4)
            print(f'Archivo {self.ruta_json_devices} actualizado.')
        
        # Procesa solo un dispositivo
        else:
            if idDevice not in self.jsonDevices:
                raise Exception("el ID no es correcto")
            data = mDNS(idDevice)
            if 'data1' in data and 'data2' in data and 'data3' in data:
                data['data'] = data['data1'] + data['data2'] + data['data3']
                for key in ['data1', 'data2', 'data3']:
                    data.pop(key)
            elif 'data1' in data and 'data2' in data:
                data['data'] = data['data1'] + data['data2']
                for key in ['data1', 'data2']:
                    data.pop(key)
            elif 'data1' in data:
                data['data'] = data['data1']
                data.pop('data1')
            
            keyDevice = self.jsonDevices[idDevice]['ewelinkData']['devicekey']
            if 'data' in data:
                data = decrypt(payload=data, devicekey=keyDevice)
            self.jsonDevices[idDevice]['state'] = data
            self.jsonDevices[idDevice]['extra']['datetime'] = datetime.datetime.now().isoformat()
            with open(self.ruta_json_devices, 'w', encoding='utf-8') as f:
                json.dump(self.jsonDevices, f, ensure_ascii=False, indent=4)
            print(f'Archivo {self.ruta_json_devices} actualizado.')
        
        return self.jsonDevices
    
    def dividir_por_tipo_y_guardar(self):

        if not self.jsonDevices:
            raise Exception('Se tiene que lanzar primero get_devices() para obtener los dispositivos')
        for device_id, device_data in self.jsonDevices.items():
            if "state" not in device_data:
                raise Exception(f'El dispositivo {device_id} no tiene la propiedad "state", tienes que lanzar get_state_devices()')
        tipos = []
        for tipo, dispositivos in self.dividir_por_tipo().items():
            tipos.append(tipo)
            nombre_archivo = self.ruta_json_devices.replace('devices',tipo)
            with open(nombre_archivo, 'w', encoding='utf-8') as f:
                json.dump(dispositivos, f, ensure_ascii=False, indent=2)

        return tipos

    def dividir_por_tipo(self, tipo=None):

        if not self.jsonDevices:
            raise Exception('Se tiene que lanzar primero get_devices() para obtener los dispositivos')
        for device_id, device_data in self.jsonDevices.items():
            if "state" not in device_data:
                raise Exception(f'El dispositivo {device_id} no tiene la propiedad "state", tienes que lanzar get_state_devices()')

        # Diccionario para agrupar por productModel
        por_tipo = {}

        for device_id, device_data in self.jsonDevices.items():
            # Accede a la propiedad productModel
            product_model = device_data.get('ewelinkData', {}).get('productModel', 'UNKNOWN')
            if tipo and product_model != tipo:
                continue
            # Crea el grupo si no existe
            if product_model not in por_tipo:
                por_tipo[product_model] = {}
            # Añade el dispositivo al grupo correspondiente
            por_tipo[product_model][device_id] = device_data

        return por_tipo
    
    def dividir_por_tipo_sqlite(self, tipo=None):
        if not hasattr(self, "ruta_SQLite_devices") or not self.ruta_SQLite_devices:
            raise Exception("Debes definir primero self.ruta_SQLite_devices con la ruta al archivo SQLite")

        conn = sqlite3.connect(self.ruta_SQLite_devices)
        cursor = conn.cursor()

        # Obtener lista de tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tablas = [row[0] for row in cursor.fetchall()]

        if not tablas:
            conn.close()
            raise Exception("El archivo SQLite no contiene tablas (capas)")

        por_tipo = {}

        for tabla in tablas:
            # Si se pide un tipo concreto, saltar las demás
            if tipo and tabla != tipo:
                continue

            cursor.execute(f"SELECT * FROM {tabla};")
            registros = cursor.fetchall()
            columnas = [desc[0] for desc in cursor.description]

            # Guardamos registros como lista de dicts
            por_tipo[tabla] = [dict(zip(columnas, row)) for row in registros]

        conn.close()
        return por_tipo

    def obtener_tipos(self):
        if not self.jsonDevices:
            raise Exception('Se tiene que lanzar primero get_devices() para obtener los dispositivos')
        for device_id, device_data in self.jsonDevices.items():
            if "state" not in device_data:
                raise Exception(f'El dispositivo {device_id} no tiene la propiedad "state", tienes que lanzar get_state_devices()')

        por_tipo = {}
        for device_id, device_data in self.jsonDevices.items():
            product_model = device_data.get('ewelinkData', {}).get('productModel', 'UNKNOWN')
            if product_model not in por_tipo:
                por_tipo[product_model] = {}
            por_tipo[product_model][device_id] = device_data

        return list(por_tipo.keys())
    
    def obtener_tipos_sqlite(self):
        if not hasattr(self, "ruta_SQLite_devices") or not self.ruta_SQLite_devices:
            raise Exception("Debes definir primero self.ruta_SQLite_devices con la ruta al archivo SQLite")

        conn = sqlite3.connect(self.ruta_SQLite_devices)
        cursor = conn.cursor()

        # Obtener todas las tablas de la base de datos (cada tabla es un 'tipo')
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tablas = [row[0] for row in cursor.fetchall()]

        conn.close()

        if not tablas:
            raise Exception("El archivo SQLite no contiene tablas (capas)")

        return tablas
    
    def jsonDevices2SQLite(self, ruta_SQLite_devices=None):
        """
        Guarda los datos de los dispositivos en un archivo SQLite.
        Crea una tabla por cada tipo y añade una fila por cada dispositivo.
        """
        if not ruta_SQLite_devices:
            raise Exception('No se ha especificado la ruta del archivo SQLite')
        if not self.jsonDevices:
            raise Exception('Se tiene que lanzar primero get_devices() para obtener los dispositivos')

        if os.path.exists(ruta_SQLite_devices):
            os.remove(ruta_SQLite_devices)

        conn = sqlite3.connect(ruta_SQLite_devices)
        c = conn.cursor()

        por_tipo = self.dividir_por_tipo()
        for tipo, dispositivos in por_tipo.items():
            # Crear tabla para el tipo
            c.execute(f'''
                CREATE TABLE IF NOT EXISTS {tipo} (
                    id TEXT PRIMARY KEY,
                    extra TEXT,
                    ewelinkData TEXT,
                    state TEXT
                )
            ''')
            # Insertar cada dispositivo
            for device_id, device_data in dispositivos.items():

                extra = json.dumps(device_data.get('extra', {}))
                ewelinkData = json.dumps(device_data.get('ewelinkData', {}))
                state = json.dumps(device_data.get('state', {}))
                c.execute(f'''
                    INSERT OR REPLACE INTO {tipo} (id, extra, ewelinkData, state)
                    VALUES (?, ?, ?, ?)
                ''', (device_id, extra, ewelinkData, state))

        conn.commit()
        conn.close()
        self.ruta_SQLite_devices = ruta_SQLite_devices
        return self.ruta_SQLite_devices
    
    def actualizar_sqlite(self):
        """
        Actualiza la tabla de un archivo SQLite con los datos de los dispositivos.
        Si un dispositivo ya existe, lo actualiza. Si no existe, lo crea.
        """
        if not self.ruta_SQLite_devices:
            raise Exception('No se ha especificado la ruta del archivo SQLite')
        if not self.jsonDevices:
            raise Exception('Se tiene que lanzar primero get_devices() para obtener los dispositivos')

        conn = sqlite3.connect(self.ruta_SQLite_devices)
        c = conn.cursor()

        por_tipo = self.dividir_por_tipo()
        for tipo, dispositivos in por_tipo.items():
            # Actualizar cada dispositivo
            for device_id, device_data in dispositivos.items():
                extra = json.dumps(device_data.get('extra', {}))
                ewelinkData = json.dumps(device_data.get('ewelinkData', {}))
                state = json.dumps(device_data.get('state', {}))
                c.execute(f'''
                    INSERT OR REPLACE INTO {tipo} (id, extra, ewelinkData, state)
                    VALUES (?, ?, ?, ?)
                ''', (device_id, extra, ewelinkData, state))

        conn.commit()
        conn.close()
        self.ruta_SQLite_devices = self.ruta_SQLite_devices
        return self.ruta_SQLite_devices
    
class geojsonQuery:
    def __init__(self):
        self.geojson = {}
    
    def MRE_datos(self, MRE=[-180, -90, 180, 90]):
        """
        Filtra el geojson según un BBOX (MRE: minx, miny, maxx, maxy).
        Devuelve un GeoJSON con los features que estén dentro o que toquen al BBOX.
        Compatible con Point, MultiPoint, LineString, MultiLineString,
        Polygon, MultiPolygon y GeometryCollection.
        """
        minx, miny, maxx, maxy = MRE

        def point_in_bbox(x, y):
            return minx <= x <= maxx and miny <= y <= maxy

        def geometry_in_bbox(geometry):
            gtype = geometry["type"]
            coords = geometry.get("coordinates")

            if gtype == "Point":
                return point_in_bbox(*coords)

            elif gtype in ("MultiPoint", "LineString"):
                return any(point_in_bbox(x, y) for x, y in coords)

            elif gtype in ("MultiLineString", "Polygon"):
                return any(point_in_bbox(x, y) for ring in coords for x, y in ring)

            elif gtype == "MultiPolygon":
                return any(point_in_bbox(x, y) for poly in coords for ring in poly for x, y in ring)

            elif gtype == "GeometryCollection":
                return any(geometry_in_bbox(geom) for geom in geometry["geometries"])

            return False

        # Filtrar features
        features_filtrados = [
            f for f in self.geojson["features"]
            if geometry_in_bbox(f["geometry"])
        ]

        self.geojson = {
            "type": "FeatureCollection",
            "features": features_filtrados
        }

        return self.geojson

    def obtener_atributos(self):
        """
        Devuelve los atributos y sus tipos de self.geojson en formato:
        {
            'nombre_propiedad': {'type': 'string' | 'integer' | 'number' | 'boolean' | 'null'}
        }
        """
        if not hasattr(self, "geojson") or self.geojson is None:
            raise Exception("Primero debes cargar un geojson en self.geojson")

        # Inferir tipo a partir de valores
        def inferir_tipo(valor):
            if isinstance(valor, bool):
                return "boolean"
            elif isinstance(valor, int):
                return "integer"
            elif isinstance(valor, float):
                return "number"
            elif valor is None:
                return "null"
            else:
                return "string"

        atributos = {}
        for feature in self.geojson.get("features", []):
            for k, v in feature.get("properties", {}).items():
                tipo = inferir_tipo(v)
                if k in atributos:
                    # Si ya existía y no coincide el tipo, generalizar a string
                    if atributos[k]["type"] != tipo:
                        atributos[k]["type"] = "string"
                else:
                    atributos[k] = {"type": tipo}

        return atributos

    def crear_ID(self, nombreCampo='ID_OGR'):
        """
        Crea un campo ID en self.geojson y le asigna un valor secuencial
        a cada feature (0, 1, 2, ...).

        :param nombreCampo: nombre del campo ID a crear
        :return: geojson con el campo ID añadido
        """
        if not hasattr(self, "geojson") or self.geojson is None:
            raise Exception("Primero debes cargar un geojson en self.geojson")

        for i, feature in enumerate(self.geojson.get("features", [])):
            if "properties" not in feature:
                feature["properties"] = {}
            feature["properties"][nombreCampo] = i
            feature["id"] = i

        return self.geojson

    def obtener_objeto_porID(self, ID='ID_OGR', valorID=0):
        """
        Obtiene un objeto por su ID en self.geojson.

        :param ID: nombre del campo ID a buscar
        :param valorID: valor del ID a buscar
        :return: GeoJSON con la(s) feature(s) encontradas o None si no existe.
        """
        if not hasattr(self, "geojson") or self.geojson is None:
            raise Exception("Primero debes cargar un geojson en self.geojson")

        coincidencias = [
            f for f in self.geojson.get("features", [])
            if f.get("properties", {}).get(ID) == valorID
        ]

        if not coincidencias:
            return None
        
        self.geojson = {
            "type": "FeatureCollection",
            "features": coincidencias
        }

        return self.geojson
    
    def aplicar_filtro_sql(self, filtro_sql):
        """
        Aplica un filtro SQL-like a un GeoJSON (dict en memoria) sin librerías externas.
        Soporta: =, >, <, >=, <=, AND, OR, NOT y paréntesis.
        Detecta automáticamente números y strings (comillas simples o dobles opcionales).
        """
        if not hasattr(self, "geojson") or self.geojson is None:
            raise Exception("Primero debes cargar un geojson en self.geojson")
        geojson_obj = self.geojson
        
        # --- Paso 1: normalizar expresión ---
        expr = filtro_sql.strip()

        # Reemplazar operadores lógicos SQL por Python
        expr = re.sub(r"\bAND\b", "and", expr, flags=re.IGNORECASE)
        expr = re.sub(r"\bOR\b", "or", expr, flags=re.IGNORECASE)
        expr = re.sub(r"\bNOT\b", "not", expr, flags=re.IGNORECASE)

        # Reemplazar '=' por '==' excepto en >= o <=
        expr = re.sub(r"(?<![<>!])=(?!=)", "==", expr)

        # --- Paso 2: reemplazar campos por props['campo'] ---
        # Detectar palabras que podrían ser campos
        palabras = set(re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", expr))
        reservadas = {"and","or","not","True","False","None"}
        campos = palabras - reservadas

        for campo in campos:
            expr = re.sub(rf"\b{campo}\b", f"props.get('{campo}')", expr)

        # --- Paso 3: evaluar expresión sobre cada feature ---
        filtradas = []
        for feat in geojson_obj["features"]:
            props = feat["properties"]

            # Convertir valores numéricos si es posible
            props_eval = {}
            for k, v in props.items():
                try:
                    props_eval[k] = float(v)
                except (ValueError, TypeError):
                    props_eval[k] = v

            # Evaluar expresión
            try:
                if eval(expr, {"props": props_eval}):
                    filtradas.append(feat)
            except Exception:
                continue

        salida = copy.deepcopy(geojson_obj)
        salida["features"] = filtradas
        self.geojson = salida
        return salida

    def ordenar_por(self, campo, orden="asc"):
        if not hasattr(self, "geojson") or self.geojson is None:
            raise Exception("Primero debes cargar un geojson en self.geojson")

        geojson_obj = self.geojson
        geojson_obj["features"] = sorted(
            geojson_obj["features"],
            key=lambda f: (
                f["properties"].get(campo) is None,   # False < True → nulos primero
                str(f["properties"].get(campo, ""))   # valor normal convertido a str
            ),
            reverse=(orden == "desc"),
        )
        self.geojson = geojson_obj
        return geojson_obj

    def offset(self, offsetValue=0):
        """
        Devuelve un GeoJSON con los features de self.geojson, pero comenzando
        desde el offsetValue-ésimo (inclusivo) Si no se especifica offsetValue, se utiliza el valor de
        offsetValue.
        """
        if not hasattr(self, "geojson") or self.geojson is None:
            raise Exception("Primero debes cargar un geojson en self.geojson")

        geojson_obj = self.geojson
        geojson_obj["features"] = geojson_obj["features"][offsetValue:]
        self.geojson = geojson_obj
        return geojson_obj
    
    def limit(self,limitValue):
        if not hasattr(self, "geojson") or self.geojson is None:
            raise Exception("Primero debes cargar un geojson en self.geojson")

        geojson_obj = self.geojson
        geojson_obj["features"] = geojson_obj["features"][:limitValue]
        self.geojson = geojson_obj
        return geojson_obj

    def obtenerAtributos(self, listaAtributos):
        if not hasattr(self, "geojson") or self.geojson is None:
            raise Exception("Primero debes cargar un geojson en self.geojson")

        geojson_obj = self.geojson
        geojson_obj["features"] = [
            {k: v for k, v in f["properties"].items() if k in listaAtributos}
            for f in geojson_obj["features"]
        ]
        self.geojson = geojson_obj
        return geojson_obj

    def borrar_geometria(self):
        if not hasattr(self, "geojson") or self.geojson is None:
            raise Exception("Primero debes cargar un geojson en self.geojson")

        geojson_obj = self.geojson
        geojson_obj["features"] = [
            {k: v for k, v in f["properties"].items()}
            for f in geojson_obj["features"]
        ]
        self.geojson = geojson_obj
        return geojson_obj

class FuenteDatosSonoff(infoSonoff,geojsonQuery):
    """
    Clase para gestionar la lectura, consulta y exportación de datos provenientes de IoT Sonoff.


    """
    def __init__(self, ruta_json_params, ruta_json_devices):
        super().__init__(ruta_json_params)

        with open(ruta_json_params, 'r', encoding='utf-8') as f:
            try:
                jsonParams = json.load(f)
            except json.JSONDecodeError:
                raise Exception(f,"json incorrecto: {ruta_json_params}")
        
        with open(ruta_json_devices, 'r', encoding='utf-8') as f:
            try:
                jsonDevices = json.load(f)
            except json.JSONDecodeError:
                raise Exception(f,"json incorrecto: {ruta_json_devices}")

        self.ruta_json_conex = ruta_json_params
        self.ruta_json_devices = ruta_json_devices
        self.jsonParams = jsonParams
        self.jsonDevices = jsonDevices
        self.capas = self.obtener_tipos()
        self.porTipo = self.dividir_por_tipo()

    def leer(self, capa=None, datasetCompleto=False):
        """
        Lee los dispositivos del tipo especificado o de todos los tipos.

        Parámetros:
        capa (str): El tipo de dispositivo a leer. Si no se especifica, se leerán todos los tipos.
        datasetCompleto (bool): Si es True, se leerán todos los dispositivos de todos los tipos.

        Retorna:
        dict: Un diccionario con los dispositivos divididos por tipo.
        """
        # Si se leen todos los dispositivos de todos los tipos
        if datasetCompleto and capa is None:
            self.porTipo = self.dividir_por_tipo()
            return self.porTipo 
        # Si no se especifica el tipo de dispositivo, se leerán los dispositivos del primer tipo
        elif capa is None and datasetCompleto is None:
            capa =  self.capas[0]
            self.porTipo = self.dividir_por_tipo(tipo=capa)
            return self.porTipo 
        # Si se especifica un tipo de dispositivo, se leerán los dispositivos de ese tipo
        else:
            if isinstance(capa, int):
                capa = self.capas[capa]
            self.porTipo = self.dividir_por_tipo(tipo=capa)
            return self.porTipo 
        
    def exportar_geojson(self, capa=None):
        """
        Exporta los dispositivos de una capa a formato GeoJSON.
        Si capa es None, usa la primera llave padre.
        """
        if not capa:
            capa = next(iter(self.porTipo.keys()))
        if isinstance(capa, int):
                tipo = self.capas[capa]
        dispositivos = self.porTipo.get(capa, {})

        features = []
        for device_id, device in dispositivos.items():
            extra = device.get('extra', {})
            lon = extra.get('long')
            lat = extra.get('lat')
            datetime = extra.get('datetime')
            if lon is None or lat is None:
                continue  # Salta si no hay coordenadas

            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat]
                },
                "properties": {
                    "id": device_id,
                    "datetime":datetime,
                    "ewelinkData": device.get('ewelinkData', {}),
                    "state": device.get('state', {})
                }
            }
            features.append(feature)

        geojson = {
            "type": "FeatureCollection",
            "features": features
        }
        self.geojson = geojson
        return geojson
    
class FuenteDatosSonoff_SQLITE(infoSonoff,geojsonQuery):
    def __init__(self, ruta_json_params, ruta_SQLite_devices):
        super().__init__(ruta_json_params)
        self.ruta_SQLite_devices = ruta_SQLite_devices

        with open(ruta_json_params, 'r', encoding='utf-8') as f:
            try:
                jsonParams = json.load(f)
            except json.JSONDecodeError:
                raise Exception(f,"json incorrecto: {ruta_json_params}")
        
        if not self.ruta_SQLite_devices:
            raise Exception('No se ha especificado la ruta del archivo SQLite')
        
        self.ruta_json_conex = ruta_json_params
        self.jsonParams = jsonParams
        self.capas = self.obtener_tipos_sqlite()
        self.porTipo = {}

    def leer(self, capa=None, datasetCompleto=False):
        if not self.ruta_SQLite_devices:
            raise Exception('No se ha especificado la ruta del archivo SQLite')
        if not os.path.exists(self.ruta_SQLite_devices):
            raise Exception(f'No se ha encontrado el archivo {self.ruta_SQLite_devices}')

        conn = sqlite3.connect(self.ruta_SQLite_devices)
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tablas = c.fetchall()
        self.capas = [tabla[0] for tabla in tablas]
        self.porTipo = {tabla[0]: {} for tabla in tablas}

        if capa is None:
            for tabla in tablas:
                if datasetCompleto:
                    c.execute(f"SELECT * FROM {tabla[0]}")
                    filas = c.fetchall()
                    for fila in filas:
                        self.porTipo[tabla[0]][fila[0]] = {
                            "extra": json.loads(fila[1]),
                            "ewelinkData": json.loads(fila[2]),
                            "state": json.loads(fila[3])
                        }
                else:
                    c.execute(f"SELECT id FROM {tabla[0]}")
                    ids = [fila[0] for fila in c.fetchall()]
                    self.porTipo[tabla[0]] = ids
        else:
            if capa not in self.capas:
                raise Exception(f'No existe la tabla {capa} en el archivo SQLite')
            if datasetCompleto:
                c.execute(f"SELECT * FROM {capa}")
                filas = c.fetchall()
                for fila in filas:
                    self.porTipo[capa][fila[0]] = {
                        "extra": json.loads(fila[1]),
                        "ewelinkData": json.loads(fila[2]),
                        "state": json.loads(fila[3])
                    }
            else:
                c.execute(f"SELECT id FROM {capa}")
                ids = [fila[0] for fila in c.fetchall()]
                self.porTipo[capa] = ids

        conn.close()
        return self.porTipo 

    def exportar_geojson(self, capa=None):
        """
        Exporta los dispositivos de una capa a formato GeoJSON.
        Si capa es None, usa la primera llave padre.
        """
        if not self.ruta_SQLite_devices:
            raise Exception('No se ha especificado la ruta del archivo SQLite')
        if not os.path.exists(self.ruta_SQLite_devices):
            raise Exception(f'No se ha encontrado el archivo {self.ruta_SQLite_devices}')

        conn = sqlite3.connect(self.ruta_SQLite_devices)
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tablas = c.fetchall()
        self.capas = [tabla[0] for tabla in tablas]

        if not capa:
            capa = next(iter(self.capas))
        if isinstance(capa, int):
            capa = self.capas[capa]
        if capa not in self.capas:
            raise Exception(f'No existe la tabla {capa} en el archivo SQLite')

        c.execute(f"SELECT * FROM {capa}")
        filas = c.fetchall()

        features = []
        for fila in filas:
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [json.loads(fila[1])['long'], json.loads(fila[1])['lat']]
                },
                "properties": {
                    "id": fila[0],
                    "datetime":json.loads(fila[1])['datetime'],
                    "ewelinkData": json.loads(fila[2]),
                    "state": json.loads(fila[3])
                }
            }
            features.append(feature)

        geojson = {
            "type": "FeatureCollection",
            "features": features
        }
        conn.close()
        self.geojson = geojson
        return geojson
  
class FuenteDatosSonoff_OGR(infoSonoff,FuenteDatosVector):
    """
    Clase para gestionar la lectura, consulta y exportación de ddatos provenientes de IoT Sonoff.


    """

    def __init__(self, ruta_json_params, ruta_SQLite_devices):
        infoSonoff.__init__(self, ruta_json_params)
        FuenteDatosVector.__init__(self, ruta_SQLite_devices)
        self.ruta_sqlite = ruta_SQLite_devices
        
    def leer(self, capa=None, EPSG_Entrada=4326, datasetCompleto=False):
        """
        Convierte tablas SQLite con campos longitud/latitud en dataset OGR en memoria con geometría puntual.

        Parámetros:
            capa (str | None): nombre de la capa a leer. Si None se comporta según datasetCompleto.
            EPSG_Entrada (int): EPSG del sistema de referencia de entrada (por defecto 4326).
            datasetCompleto (bool): si True, procesa todas las capas; si False, sólo la primera.

        Devuelve:
            out_ds (ogr.DataSource): dataset en memoria con geometrías construidas.
        """
        # Abrir dataset SQLite de entrada
        ds = ogr.Open(self.ruta_sqlite)
        if ds is None:
            raise RuntimeError(f"No se pudo abrir la base de datos {self.ruta_sqlite}")

        # Crear dataset en memoria
        outdriver = ogr.GetDriverByName("MEMORY")
        out_ds = outdriver.CreateDataSource("out_mem")

        # Definir SRS
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(EPSG_Entrada)

        def procesar_capa(in_layer, nombre_capa):
            # Crear capa de salida en memoria
            out_layer = out_ds.CreateLayer(nombre_capa, srs, ogr.wkbPoint)

            # Copiar campos
            in_defn = in_layer.GetLayerDefn()
            for i in range(in_defn.GetFieldCount()):
                field_defn = in_defn.GetFieldDefn(i)
                out_layer.CreateField(field_defn)

            out_defn = out_layer.GetLayerDefn()

            # Procesar features
            for in_feat in in_layer:
                extra_raw = in_feat.GetField("extra")
                extra_json = json.loads(extra_raw)
                lon = float(extra_json.get("long"))
                lat = float(extra_json.get("lat"))
                if lon is None or lat is None:
                    continue

                geom = ogr.Geometry(ogr.wkbPoint)
                geom.AddPoint(float(lon), float(lat))

                out_feat = ogr.Feature(out_defn)
                out_feat.SetGeometry(geom)

                # Copiar atributos
                for i in range(out_defn.GetFieldCount()):
                    out_feat.SetField(out_defn.GetFieldDefn(i).GetNameRef(),
                                    in_feat.GetField(i))

                out_layer.CreateFeature(out_feat)
                out_feat = None

            in_layer.ResetReading()

        # Selección de capas según parámetros
        if capa is not None:
            try:
                idx = int(capa)
                layer = ds.GetLayerByIndex(idx)
            except (ValueError, TypeError):
                layer = ds.GetLayer(capa)
            if layer is None:
                raise Exception(f"No existe la capa '{capa}'")
            
            in_layer = ds.GetLayer(capa)
            if in_layer is None:
                raise ValueError(f"La capa {capa} no existe en {self.ruta_sqlite}")
            procesar_capa(in_layer, in_layer.GetName())
            self.multiLayers = False

        elif datasetCompleto:
            for i in range(ds.GetLayerCount()):
                in_layer = ds.GetLayerByIndex(i)
                procesar_capa(in_layer, in_layer.GetName())
                self.multiLayers = True

        else:
            in_layer = ds.GetLayerByIndex(0)
            procesar_capa(in_layer, in_layer.GetName())
            self.multiLayers = False

        self.datasource = out_ds
        return out_ds