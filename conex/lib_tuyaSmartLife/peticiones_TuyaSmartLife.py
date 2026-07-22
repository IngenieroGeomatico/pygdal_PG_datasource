import tinytuya
import json


def discover_tuya_all(scan_time=60):
    """
    Escanea la red local usando TinyTuya y devuelve un diccionario de dispositivos.

    Parámetros
    ----------
    scan_time : int, opcional
        Segundos que dura el escaneo de red (por defecto 60).

    Retorna
    -------
    dict
        {
            id: {
                'ip': <IP>,
                'productKey': <productKey>,
                'ver': <3.3|3.1>,
                'encrypt': <True|False>,
                'name': <nombre>,
                'raw': <datos en crudo>,
            },
            ...
        }
    """
    dispositivos = tinytuya.deviceScan(scantime=scan_time)

    # Agregar raw con datos UDP simples (opcional)
    result = {}
    for ip, info in dispositivos.items():
        result[info['id']] = {
            "ip": ip,
            "productKey": info.get("productKey"),
            "ver": info.get("ver"),
            "encrypt": info.get("encrypt"),
            "name": info.get("name", ""),
            "raw": None  # Puedes llenarlo si quieres hacer broadcast UDP aparte
        }
    return result


def find_all_devices(scan_tcp=True, scantime=60):
    """
    Descubre todos los dispositivos Tuya en la red local.

    Función de conveniencia usada por ``infoTuyaSmartLife.get_devices``. Envuelve
    a :func:`discover_tuya_all` manteniendo la firma esperada por el llamador.

    Parámetros
    ----------
    scan_tcp : bool, opcional
        Reservado para compatibilidad (TinyTuya realiza el descubrimiento por
        broadcast UDP). Se mantiene por compatibilidad de firma.
    scantime : int, opcional
        Segundos que dura el escaneo de red (por defecto 60).

    Retorna
    -------
    dict
        Diccionario de dispositivos indexado por ``id`` (ver ``discover_tuya_all``).
    """
    return discover_tuya_all(scan_time=scantime)


def discover_tuya_by_id_or_ip(dev_id=None, ip=None, scan_time=60):
    """
    Busca un dispositivo específico por Device ID o IP usando TinyTuya.
    Retorna los mismos campos que discover_tuya_all.
    """
    all_devices = discover_tuya_all(scan_time=scan_time)

    for device_id, info in all_devices.items():
        if (dev_id and device_id == dev_id) or (ip and info["ip"] == ip):
            return info
    return None


if __name__ == "__main__":
    # Ejemplo de uso: escaneo completo
    devices = discover_tuya_all()
    print(json.dumps(devices, indent=4))

    # # Ejemplo de búsqueda por ID
    # some_id = "bxxxxxx24bcaae3b498eiajc"
    # device_info = discover_tuya_by_id_or_ip(dev_id=some_id)
    # print(json.dumps(device_info, indent=4))
