import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from conex.sonoff_conex import FuenteDatosSonoff_DualR3
from conex.sonoff_conex import infoSonoff


ruta_json_conex = os.path.join(os.path.dirname(__file__), 'files/sonoff.json')
ruta_json_params = os.path.join(os.path.dirname(__file__), 'files/params_sonoff.json')
infoSonoff = infoSonoff(
    ruta_json_params=ruta_json_params
)

# FuenteDatosSonoff_DualR3 = FuenteDatosSonoff_DualR3(
#     ruta_json_conex=ruta_json_conex, 
#     ruta_json_params=ruta_json_params
# )