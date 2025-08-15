"""HTTP requests utilities for Sonoff devices."""
import requests
import time
from zeroconf import ServiceBrowser, Zeroconf, ServiceListener
from typing import Any, Dict, Optional

def sonoffPost(url: str, body: dict, header: dict) -> Any:
    """
    Realiza una petición POST y devuelve la respuesta en formato JSON.

    Args:
        url (str): URL de destino.
        body (dict): Cuerpo de la petición.
        header (dict): Cabeceras HTTP.

    Returns:
        Any: Respuesta decodificada en JSON.
    """
    time_out = 5
    response = requests.post(url, headers=header, json=body, timeout=time_out)
    response.raise_for_status()
    return response.json()

def mDNS(idDevice: str, timeout: int = 20, intentos: int = 3) -> Optional[Dict]:
    """
    Busca un dispositivo Sonoff por ID usando mDNS, repitiendo el escaneo varios intentos.

    Args:
        idDevice (str): ID del dispositivo a buscar.
        timeout (int): segundos máximos de espera por intento.
        intentos (int): número de repeticiones del escaneo.

    Returns:
        Optional[Dict]: Propiedades del dispositivo si se encuentra, None si no.
    """
    for i in range(intentos):
        print(f"Intento mDNS {i+1}/{intentos}")

        class MyListener(ServiceListener):
            def __init__(self, idDevice):
                self.idDevice = idDevice
                self.properties = None
                self.found = False

            def add_service(self, zeroconf, service_type, name):
                info = zeroconf.get_service_info(service_type, name)
                if info:
                    id_address = info.decoded_properties.get("id")
                    if id_address == self.idDevice:
                        self.properties = info.decoded_properties
                        self.found = True

            def remove_service(self, zeroconf, service_type, name):
                pass

        zeroconf = Zeroconf()
        listener = MyListener(idDevice)
        service_type = "_ewelink._tcp.local."
        ServiceBrowser(zeroconf, service_type, listener=listener)

        start_time = time.time()
        while not listener.found and (time.time() - start_time) < timeout:
            time.sleep(0.2)

        zeroconf.close()
        if listener.found:
            print(f"Dispositivo {idDevice} encontrado en el intento {i+1}/{intentos}")
            return listener.properties

    print(f"Dispositivo {idDevice} no encontrado tras {intentos} intentos.")
    return None

def mDNS_todos(devices: Dict, timeout: int = 20, intentos: int = 3) -> Dict[str, Dict]:
    """
    Busca todos los dispositivos Sonoff en la red local usando mDNS, repitiendo el escaneo varios intentos.

    Args:
        devices (dict): json con los dispositivos.
        timeout (int): segundos máximos de espera por intento.
        intentos (int): número de repeticiones del escaneo.

    Returns:
        Dict[str, Dict]: Diccionario con las propiedades de cada dispositivo.
    """
    encontrados = {}
    for i in range(intentos):
        print(f"Intento mDNS_todos {i+1}/{intentos}")

        class MyListener(ServiceListener):
            def __init__(self):
                self.propertiesJSON = {}

            def add_service(self, zeroconf, service_type, name):
                info = zeroconf.get_service_info(service_type, name)
                if info:
                    ip_address = ".".join(map(str, info.addresses[0]))
                    properties = info.decoded_properties
                    properties['IP'] = ip_address
                    self.propertiesJSON[properties.get('id', name)] = properties

            def remove_service(self, zeroconf, service_type, name):
                pass

        numDevices = len(devices)
        zeroconf = Zeroconf()
        listener = MyListener()
        service_type = "_ewelink._tcp.local."
        ServiceBrowser(zeroconf, service_type, listener=listener)

        start_time = time.time()
        while len(listener.propertiesJSON) < numDevices and (time.time() - start_time) < timeout:
            time.sleep(0.2)

        zeroconf.close()
        encontrados.update(listener.propertiesJSON)
        if len(encontrados) >= numDevices:
            break

    print(f"Dispositivos encontrados tras {i+1}/{intentos} intentos: {len(encontrados)} de {numDevices}")
    return encontrados
