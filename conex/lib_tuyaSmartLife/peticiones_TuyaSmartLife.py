import tinytuya
import socket
import json

def discover_tuya_all():
    """
    Escanea la red local usando TinyTuya y devuelve un diccionario de dispositivos.
    Devuelve:
        {
            id: {
                'ip': <IP>,
                'productKey': <productKey>,
                'ver': <3.3|3.1>,
                'encrypt': <True|False>,
                'raw': <datos en crudo>,
                ...
            },
            ...
        }
    """
    dispositivos = tinytuya.deviceScan()
    
    # Agregar raw con datos UDP simples (opcional)
    result = {}
    for ip, info in dispositivos.items():
        print(ip, info)
        result[info['id']] = {
            "ip": ip,
            "productKey": info.get("productKey"),
            "ver": info.get("ver"),
            "encrypt": info.get("encrypt"),
            "name": info.get("name", ""),
            "raw": None  # Puedes llenarlo si quieres hacer broadcast UDP aparte
        }
    return result


def discover_tuya_by_id_or_ip(dev_id=None, ip=None, scan_time=60):
    """
    Busca un dispositivo específico por Device ID o IP usando TinyTuya.
    Retorna los mismos campos que discover_tuya_all.
    """
    all_devices = discover_tuya_all(scan_time=scan_time)
    
    for device_ip, info in all_devices.items():
        if (dev_id and info["id"] == dev_id) or (ip and device_ip == ip):
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
