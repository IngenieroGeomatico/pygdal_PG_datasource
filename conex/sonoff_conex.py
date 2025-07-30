
# Python
import os
import sys
import json
import hmac
import base64
import hashlib
import requests


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

        print(jsonParams)


    # Funciones

    def makeSign(self, key, message):
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
        print(resp)
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

    def get_devices(self, auth: dict):
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
            return devices


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

