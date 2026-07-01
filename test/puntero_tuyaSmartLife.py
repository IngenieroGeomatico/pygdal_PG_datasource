import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from conex.tuyaSmartLife_conex import infoTuyaSmartLife


ruta_json_params = os.path.join(os.path.dirname(__file__), 'files/params_tuyaSmartLife.json')
ruta_json_devices = os.path.join(os.path.dirname(__file__), 'files/devices_tuyaSmartLife.json')
ruta_SQLite_devices = os.path.join(os.path.dirname(__file__), 'files/devices_tuyaSmartLife.sqlite')


# Conexión y parámetro at:

infoTuyaSmartLife = infoTuyaSmartLife(
    ruta_json_params=ruta_json_params
)
# print('at: ', infoTuyaSmartLife.auth)
# print('--- -- -- -- - - - --- --- -- - - -')

# print('refresh at: ', infoTuyaSmartLife.refreshAT())
# print('--- -- -- -- - - - --- --- -- - - -')

# print('devices: ', infoTuyaSmartLife.get_devices(ruta_json_devices = ruta_json_devices ))
# print('--- -- -- -- - - - --- --- -- - - -')

print('devices state: ', infoTuyaSmartLife.get_state_devices())
print('--- -- -- -- - - - --- --- -- - - -')

