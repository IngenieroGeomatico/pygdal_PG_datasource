# Python
import os
import re
import sys
import json
import hmac
import copy
import uuid
import time
import base64
import sqlite3
import hashlib
import requests
import datetime
from urllib.parse import quote

# Import diferido de GDAL/OGR y del descubrimiento local (tinytuya), para que
# importar este módulo no aborte el proceso cuando faltan esas dependencias.
try:
    from osgeo import ogr, osr, gdal
    _GDAL_IMPORT_ERROR = None
except Exception as _exc:  # pragma: no cover - depende del entorno
    ogr = osr = gdal = None
    _GDAL_IMPORT_ERROR = _exc

try:
    from .lib_tuyaSmartLife.peticiones_TuyaSmartLife import find_all_devices
except Exception as _exc:  # pragma: no cover - depende del entorno
    find_all_devices = None
    _TINYTUYA_IMPORT_ERROR = _exc
else:
    _TINYTUYA_IMPORT_ERROR = None

from .Vector_conex import FuenteDatosVector
from .sonoff_conex import geojsonQuery, _asegurar_gdal


def _asegurar_tinytuya():
    """Lanza un error claro si el descubrimiento local (tinytuya) no está disponible."""
    if _TINYTUYA_IMPORT_ERROR is not None:
        raise ImportError(
            "El descubrimiento local de dispositivos (paquete 'tinytuya') no está disponible."
        ) from _TINYTUYA_IMPORT_ERROR

class infoTuyaSmartLife:
 

    def __init__(self, ruta_json_params=None):
        templateJSON = {
            "router":{
                'IP':'',
                'IP_2':'',
                'SSID':'',
                'pass':'',
                'pass_R':''
            },
            "tuyaSmartLife":{
                'user_':'',
                'password':'',
                'url':'https://developer.tuya.com/',
                'user':{
                    'AccessID':'',
                    'AccessSecret':''
                }
            }
        }

        # Constantes
        self.region = {
            'base': "https://openapi.tuya.com",
            'China Data Center': 'https://openapi.tuyacn.com',
            'Western America Data Center': 'https://openapi.tuyaus.com',
            'Eastern America Data Center': 'https://openapi-ueaz.tuyaus.com',
            'Central Europe Data Center': 'https://openapi.tuyaeu.com',
            'Western Europe Data Center':'https://openapi-weaz.tuyaeu.com',
            'India Data Center':'https://openapi.tuyain.com'	
        }

        self.ruta_json_params = None
        self.jsonParams = None
        self.auth = None
        self.ruta_json_devices = None
        self.jsonDevices = None
        self.ruta_SQLite_devices = None

        if not ruta_json_params:
            dir_base = os.path.dirname(os.path.abspath(__file__))
            ruta_json_params = os.path.join(dir_base, 'lib_tuyaSmartLife/params_tuyaSmartLife.json')

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
        if not jsonParams["tuyaSmartLife"]["user_"]:
            raise ValueError('El campo "user_" no puede estar vacío en el archivo de parámetros.')
        if not jsonParams["tuyaSmartLife"]["password"]:
            raise ValueError('El campo "password" no puede estar vacío en el archivo de parámetros.')
        if not jsonParams["tuyaSmartLife"]["user"]["AccessID"]:
            raise ValueError('El campo "AccessID" no puede estar vacío en el archivo de parámetros.')
        if not jsonParams["tuyaSmartLife"]["user"]["AccessSecret"]:
            raise ValueError('El campo "AccessSecret" no puede estar vacío en el archivo de parámetros.')
        
        jsonParams["tuyaSmartLife"].update(self.login())
        with open(ruta_json_params, 'w', encoding='utf-8') as f:
            json.dump(jsonParams, f, ensure_ascii=False, indent=4)


        return

    # Funciones
    def calc_sign(self, msg, key):
        """Calcula el HMAC-SHA256 y devuelve en mayúsculas."""
        return hmac.new(
            msg=msg.encode("utf-8"),
            key=key.encode("utf-8"),
            digestmod=hashlib.sha256
        ).hexdigest().upper()

    def generate_payload(self, method, uri, body=""):
        """
        Genera la parte de stringToSign (sin client_id ni timestamp)
        """
        if not body:
            body_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        else:
            body_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
        return f"{method}\n{body_hash}\n\n{uri}"

    def _build_uri(self, path, params=None):
        """Construye la URI con query string canónica ordenada alfabéticamente"""
        if not params:
            return path
        items = []
        for k, v in sorted(params.items()):
            if v is None:
                continue
            k_enc = quote(str(k), safe='-_.~')
            v_enc = quote(str(v), safe='-_.~')
            items.append(f"{k_enc}={v_enc}")
        return f"{path}?{'&'.join(items)}"

    def call_api(self, method, path, params=None, body=None, use_token=True):
        """
        Llama a cualquier endpoint de Tuya Cloud con firma correcta.
        """
        client_id = self.jsonParams["tuyaSmartLife"]["user"]["AccessID"]
        secret = self.jsonParams["tuyaSmartLife"]["user"]["AccessSecret"]
        access_token = self.auth.get("access_token") if use_token else ""

        uri = self._build_uri(path, params)
        regionURL = self.region['Central Europe Data Center']
        url = regionURL + uri
        t = str(int(time.time() * 1000))

        string_to_sign = self.generate_payload(method, uri, body)

        # Firma según si se usa token o no
        if use_token and access_token:
            # Business API: client_id + access_token + t + string_to_sign
            sign_input = f"{client_id}{access_token}{t}{string_to_sign}"
        else:
            # Login / refresh: client_id + t + string_to_sign
            sign_input = f"{client_id}{t}{string_to_sign}"

        sign = self.calc_sign(sign_input, secret)

        headers = {
            "client_id": client_id,
            "sign": sign,
            "t": t,
            "sign_method": "HMAC-SHA256",
        }

        if use_token and access_token:
            headers["access_token"] = access_token
        if body:
            headers["Content-Type"] = "application/json"

        resp = requests.request(method, url, headers=headers, json=body)
        return resp.json()

    def _string_to_sign(self, method, uri, body=""):
        body_hash = hashlib.sha256(body.encode("utf-8")).hexdigest() if body else "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        return f"{method}\n{body_hash}\n\n{uri}"
    
    def call_v2_api(self, path, method="GET", params=None, body=None):
        """
        Llamada genérica a un endpoint V2 de Tuya con firma correcta.
        """
        client_id = self.jsonParams["tuyaSmartLife"]["user"]["AccessID"]
        secret = self.jsonParams["tuyaSmartLife"]["user"]["AccessSecret"]
        access_token = self.auth.get("access_token")
        if not access_token:
            raise ValueError("No hay access_token. Ejecuta login() o refreshAT().")

        uri = self._build_uri(path, params)
        regionURL = self.region['Central Europe Data Center']
        url = regionURL + uri
        t = str(int(time.time() * 1000))

        string_to_sign = self._string_to_sign(method, uri, body or "")
        sign_input = f"{client_id}{access_token}{t}{string_to_sign}"
        sign = self.calc_sign(sign_input, secret)

        headers = {
            "client_id": client_id,
            "access_token": access_token,
            "sign": sign,
            "t": t,
            "sign_method": "HMAC-SHA256",
            "mode": "cors",
            "Content-Type": "application/json"
        }

        resp = requests.request(method, url, headers=headers, json=body)
        return resp.json()

    def login(self):
        result = self.call_api("GET", "/v1.0/token", params={"grant_type": 1}, use_token=False)
        self.auth = result.get("result", {})
        return self.auth

    def refreshAT(self):
        refresh_token = self.auth.get("refresh_token")
        if not refresh_token:
            raise ValueError("No hay refresh_token disponible. Ejecuta primero login().")
        result = self.call_api("GET", f"/v1.0/token/{refresh_token}", use_token=False)
        self.auth = result.get("result", {})
        return self.auth

    def get_devices(self, product_ids=None, categories=None, page_size=20, last_id=None, ruta_json_devices=None, readOnlyJSON=False):
        
        with open(ruta_json_devices, 'r', encoding='utf-8') as f:
            try:
                jsonDevices = json.load(f)
                self.ruta_json_devices = ruta_json_devices
                self.jsonDevices = jsonDevices
                if readOnlyJSON:
                    return jsonDevices
            except json.JSONDecodeError:
                jsonDevices = {}

        params = {"page_size": page_size}
        if product_ids:
            params["product_ids"] = ",".join(product_ids[:5])
        if categories:
            params["categories"] = ",".join(categories[:5])
        if last_id:
            params["last_id"] = last_id

        devices = self.call_v2_api("/v2.0/cloud/thing/device", params=params)["result"]

        _asegurar_tinytuya()
        localDevices = find_all_devices(scan_tcp=True, scantime=120)

        for device in devices:
            templateJSONDevice = {
                'extra': {
                    'long':0,
                    'lat':0
                },
                'tuyaSmartLife': device
            }

            # Inicializamos parent_id en None
            if device.get('sub'):
                templateJSONDevice['extra']['parent_id'] = None

            if not device['id'] in jsonDevices:
                jsonDevices[device['id']] = templateJSONDevice
            else:
                jsonDevices[device['id']]["tuyaSmartLife"] = device


        # Guardamos en JSON
        if not ruta_json_devices:
            dir_base = os.path.dirname(os.path.abspath(__file__))
            ruta_json_devices = os.path.join(dir_base, 'lib_tuyaSmartLife/devices_tuyaSmartLife.json')

        with open(ruta_json_devices, 'w', encoding='utf-8') as f:
            json.dump(jsonDevices, f, ensure_ascii=False, indent=4)

        self.ruta_json_devices = ruta_json_devices
        self.jsonDevices = jsonDevices
        return jsonDevices
    

    def get_state_devices(self, idDevice=None):
        if not self.jsonDevices:
            raise Exception('Ejecuta get_devices() primero para obtener los dispositivos')
        if idDevice:
            if idDevice not in self.jsonDevices:
                raise Exception(f"Dispositivo '{idDevice}' no encontrado")
            result = self.call_v2_api(f"/v1.0/devices/{idDevice}/status")
            self.jsonDevices[idDevice]['state'] = result.get('result', [])
            return self.jsonDevices[idDevice]
        else:
            for device_id in self.jsonDevices:
                result = self.call_v2_api(f"/v1.0/devices/{device_id}/status")
                self.jsonDevices[device_id]['state'] = result.get('result', [])
            return self.jsonDevices

    def dividir_por_tipo(self, tipo=None):
        if not self.jsonDevices:
            raise Exception('Ejecuta get_devices() primero para obtener los dispositivos')
        por_tipo = {}
        for device_id, device_data in self.jsonDevices.items():
            raw = device_data.get('tuyaSmartLife', {})
            category = raw.get('category', 'UNKNOWN')
            if tipo and category != tipo:
                continue
            if category not in por_tipo:
                por_tipo[category] = {}
            por_tipo[category][device_id] = device_data
        return por_tipo

    def dividir_por_tipo_y_guardar(self):
        if not self.jsonDevices:
            raise Exception('Ejecuta get_devices() primero para obtener los dispositivos')
        if not self.ruta_json_devices:
            dir_base = os.path.dirname(os.path.abspath(__file__))
            self.ruta_json_devices = os.path.join(dir_base, 'lib_tuyaSmartLife/devices_tuyaSmartLife.json')
        tipos = []
        for categoria, dispositivos in self.dividir_por_tipo().items():
            tipos.append(categoria)
            nombre_archivo = self.ruta_json_devices.replace('devices', categoria)
            with open(nombre_archivo, 'w', encoding='utf-8') as f:
                json.dump(dispositivos, f, ensure_ascii=False, indent=2)
        return tipos

    def dividir_por_tipo_sqlite(self, tipo=None):
        if not hasattr(self, 'ruta_SQLite_devices') or not self.ruta_SQLite_devices:
            raise Exception("Define self.ruta_SQLite_devices con la ruta al archivo SQLite")
        conn = sqlite3.connect(self.ruta_SQLite_devices)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tablas = [row[0] for row in cursor.fetchall()]
        if not tablas:
            conn.close()
            raise Exception("El archivo SQLite no contiene tablas")
        por_tipo = {}
        for tabla in tablas:
            if tipo and tabla != tipo:
                continue
            cursor.execute(f"SELECT * FROM {tabla};")
            registros = cursor.fetchall()
            columnas = [desc[0] for desc in cursor.description]
            por_tipo[tabla] = [dict(zip(columnas, row)) for row in registros]
        conn.close()
        return por_tipo

    def obtener_tipos(self):
        if not self.jsonDevices:
            raise Exception('Ejecuta get_devices() primero para obtener los dispositivos')
        categorias = set()
        for device_data in self.jsonDevices.values():
            raw = device_data.get('tuyaSmartLife', {})
            categorias.add(raw.get('category', 'UNKNOWN'))
        return sorted(categorias)

    def obtener_tipos_sqlite(self):
        if not hasattr(self, 'ruta_SQLite_devices') or not self.ruta_SQLite_devices:
            raise Exception("Define self.ruta_SQLite_devices con la ruta al archivo SQLite")
        conn = sqlite3.connect(self.ruta_SQLite_devices)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tablas = [row[0] for row in cursor.fetchall()]
        conn.close()
        if not tablas:
            raise Exception("El archivo SQLite no contiene tablas")
        return tablas

    def jsonDevices2SQLite(self, ruta_SQLite_devices=None):
        if not ruta_SQLite_devices:
            raise Exception('Especifica la ruta del archivo SQLite')
        if not self.jsonDevices:
            raise Exception('Ejecuta get_devices() primero para obtener los dispositivos')
        if os.path.exists(ruta_SQLite_devices):
            os.remove(ruta_SQLite_devices)
        conn = sqlite3.connect(ruta_SQLite_devices)
        c = conn.cursor()
        por_tipo = self.dividir_por_tipo()
        for categoria, dispositivos in por_tipo.items():
            c.execute(f'''
                CREATE TABLE IF NOT EXISTS {categoria} (
                    id TEXT PRIMARY KEY,
                    extra TEXT,
                    tuyaSmartLife TEXT,
                    state TEXT
                )
            ''')
            for device_id, device_data in dispositivos.items():
                extra = json.dumps(device_data.get('extra', {}))
                raw = json.dumps(device_data.get('tuyaSmartLife', {}))
                state = json.dumps(device_data.get('state', []))
                c.execute(f'''
                    INSERT OR REPLACE INTO {categoria} (id, extra, tuyaSmartLife, state)
                    VALUES (?, ?, ?, ?)
                ''', (device_id, extra, raw, state))
        conn.commit()
        conn.close()
        self.ruta_SQLite_devices = ruta_SQLite_devices
        return ruta_SQLite_devices

    def actualizar_sqlite(self):
        if not self.ruta_SQLite_devices:
            raise Exception('Ejecuta jsonDevices2SQLite() primero para crear el SQLite')
        if not self.jsonDevices:
            raise Exception('Ejecuta get_devices() primero para obtener los dispositivos')
        conn = sqlite3.connect(self.ruta_SQLite_devices)
        c = conn.cursor()
        por_tipo = self.dividir_por_tipo()
        for categoria, dispositivos in por_tipo.items():
            for device_id, device_data in dispositivos.items():
                extra = json.dumps(device_data.get('extra', {}))
                raw = json.dumps(device_data.get('tuyaSmartLife', {}))
                state = json.dumps(device_data.get('state', []))
                c.execute(f'''
                    INSERT OR REPLACE INTO {categoria} (id, extra, tuyaSmartLife, state)
                    VALUES (?, ?, ?, ?)
                ''', (device_id, extra, raw, state))
        conn.commit()
        conn.close()
        return self.ruta_SQLite_devices


class FuenteDatosTuya(infoTuyaSmartLife, geojsonQuery):
    def __init__(self, ruta_json_params, ruta_json_devices):
        infoTuyaSmartLife.__init__(self, ruta_json_params)
        with open(ruta_json_devices, 'r', encoding='utf-8') as f:
            try:
                jsonDevices = json.load(f)
            except json.JSONDecodeError:
                raise Exception(f"json incorrecto: {ruta_json_devices}")
        self.ruta_json_devices = ruta_json_devices
        self.jsonDevices = jsonDevices
        self.capas = self.obtener_tipos()
        self.porTipo = self.dividir_por_tipo()

    def leer(self, capa=None, datasetCompleto=False):
        if datasetCompleto and capa is None:
            self.porTipo = self.dividir_por_tipo()
            return self.porTipo
        elif capa is None:
            capa = self.capas[0]
            self.porTipo = self.dividir_por_tipo(tipo=capa)
            return self.porTipo
        else:
            if isinstance(capa, int):
                capa = self.capas[capa]
            self.porTipo = self.dividir_por_tipo(tipo=capa)
            return self.porTipo

    def exportar_geojson(self, capa=None):
        if not capa:
            capa = next(iter(self.porTipo.keys()))
        if isinstance(capa, int):
            capa = self.capas[capa]
        dispositivos = self.porTipo.get(capa, {})
        features = []
        for device_id, device in dispositivos.items():
            extra = device.get('extra', {})
            lon = extra.get('long')
            lat = extra.get('lat')
            if lon is None or lat is None:
                continue
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat]
                },
                "properties": {
                    "id": device_id,
                    "tuyaSmartLife": device.get('tuyaSmartLife', {}),
                    "state": device.get('state', [])
                }
            }
            features.append(feature)
        geojson = {
            "type": "FeatureCollection",
            "features": features
        }
        self.geojson = geojson
        return geojson


class FuenteDatosTuya_SQLITE(infoTuyaSmartLife, geojsonQuery):
    def __init__(self, ruta_json_params, ruta_SQLite_devices):
        infoTuyaSmartLife.__init__(self, ruta_json_params)
        self.ruta_SQLite_devices = ruta_SQLite_devices
        if not self.ruta_SQLite_devices:
            raise Exception('No se ha especificado la ruta del archivo SQLite')
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
                            "tuyaSmartLife": json.loads(fila[2]),
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
                        "tuyaSmartLife": json.loads(fila[2]),
                        "state": json.loads(fila[3])
                    }
            else:
                c.execute(f"SELECT id FROM {capa}")
                ids = [fila[0] for fila in c.fetchall()]
                self.porTipo[capa] = ids
        conn.close()
        return self.porTipo

    def exportar_geojson(self, capa=None):
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
            extra = json.loads(fila[1])
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [extra['long'], extra['lat']]
                },
                "properties": {
                    "id": fila[0],
                    "tuyaSmartLife": json.loads(fila[2]),
                    "state": json.loads(fila[3])
                }
            })
        geojson = {
            "type": "FeatureCollection",
            "features": features
        }
        conn.close()
        self.geojson = geojson
        return geojson


class FuenteDatosTuya_OGR(infoTuyaSmartLife, FuenteDatosVector):
    def __init__(self, ruta_json_params, ruta_SQLite_devices):
        infoTuyaSmartLife.__init__(self, ruta_json_params)
        FuenteDatosVector.__init__(self, ruta_SQLite_devices)
        self.ruta_sqlite = ruta_SQLite_devices

    def leer(self, capa=None, EPSG_Entrada=4326, datasetCompleto=False):
        _asegurar_gdal()
        ds = ogr.Open(self.ruta_sqlite)
        if ds is None:
            raise RuntimeError(f"No se pudo abrir la base de datos {self.ruta_sqlite}")
        outdriver = ogr.GetDriverByName("MEMORY")
        out_ds = outdriver.CreateDataSource("out_mem")
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(EPSG_Entrada)

        def procesar_capa(in_layer, nombre_capa):
            out_layer = out_ds.CreateLayer(nombre_capa, srs, ogr.wkbPoint)
            in_defn = in_layer.GetLayerDefn()
            for i in range(in_defn.GetFieldCount()):
                out_layer.CreateField(in_defn.GetFieldDefn(i))
            out_defn = out_layer.GetLayerDefn()
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
                for i in range(out_defn.GetFieldCount()):
                    out_feat.SetField(out_defn.GetFieldDefn(i).GetNameRef(), in_feat.GetField(i))
                out_layer.CreateFeature(out_feat)
                out_feat = None
            in_layer.ResetReading()

        if capa is not None:
            try:
                idx = int(capa)
                in_layer = ds.GetLayerByIndex(idx)
            except (ValueError, TypeError):
                in_layer = ds.GetLayer(capa)
            if in_layer is None:
                raise Exception(f"No existe la capa '{capa}'")
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
