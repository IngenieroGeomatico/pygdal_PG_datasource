import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from conex.sonoff_conex import FuenteDatosSonoff, FuenteDatosSonoff_SQLITE
from conex.sonoff_conex import infoSonoff


ruta_json_params = os.path.join(os.path.dirname(__file__), 'files/params_sonoff.json')
ruta_json_devices = os.path.join(os.path.dirname(__file__), 'files/devices_sonoff.json')
ruta_SQLite_devices = os.path.join(os.path.dirname(__file__), 'files/devices_sonoff.sqlite')


# Conexión y parámetro at:

infoSonoff = infoSonoff(
    ruta_json_params=ruta_json_params
)
print('at: ', infoSonoff.auth)
print('--- -- -- -- - - - --- --- -- - - -')

# dispositivos:
dispositivos = infoSonoff.get_devices( 
    auth = infoSonoff.auth, 
    ruta_json_devices = ruta_json_devices 
)
# print('dispositivos: ', dispositivos)
print('--- -- -- -- - - - --- --- -- - - -')

# estado dispositivos:
dispositivos = infoSonoff.get_state_devices()
# print('dispositivos: ', dispositivos)
print('--- -- -- -- - - - --- --- -- - - -')

# Estado 1 dispositivo
dispositivos = infoSonoff.get_state_devices(idDevice = "1001ed9559")
# print("1001ed9559: ",dispositivos["1001ed9559"])
print('--- -- -- -- - - - --- --- -- - - -')

# Dividir por tipo
tipos = infoSonoff.dividir_por_tipo_y_guardar()
print(tipos)
print('--- -- -- -- - - - --- --- -- - - -')

# Dividir por tipo
tipos = infoSonoff.dividir_por_tipo()
print(tipos)
print('--- -- -- -- - - - --- --- -- - - -')

# Dividir por tipo
tipos = infoSonoff.obtener_tipos()
print(tipos)
print('--- -- -- -- - - - --- --- -- - - -')


# guardar sqlite
tipos = infoSonoff.jsonDevices2SQLite(ruta_SQLite_devices=ruta_SQLite_devices)
print(tipos)
print('--- -- -- -- - - - --- --- -- - - -')

# guardar sqlite
tipos = infoSonoff.actualizar_sqlite()
print(tipos)
print('--- -- -- -- - - - --- --- -- - - -')





FuenteDatosSonoff_obj = FuenteDatosSonoff(
    ruta_json_devices=ruta_json_devices, 
    ruta_json_params=ruta_json_params
)

FuenteDatosSonoff_obj.leer()
gjson = FuenteDatosSonoff_obj.exportar_geojson()
print(gjson)




FuenteDatosSonoff_SQLITE_obj = FuenteDatosSonoff_SQLITE(
    ruta_SQLite_devices=ruta_SQLite_devices,
    ruta_json_params=ruta_json_params
)

FuenteDatosSonoff_SQLITE_obj.leer()
gjson = FuenteDatosSonoff_SQLITE_obj.exportar_geojson()
print(gjson)