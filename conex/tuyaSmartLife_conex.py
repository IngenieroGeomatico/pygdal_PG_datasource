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
        return
    
    def dividir_por_tipo_y_guardar(self):
        return

    def dividir_por_tipo(self):
        return
    
    def dividir_por_tipo_sqlite(self):
        return

    def obtener_tipos(self):
        return
    
    def obtener_tipos_sqlite(self):
        return
    
    def jsonDevices2SQLite(self):
        return
    
    def actualizar_sqlite(self):
        return
    

