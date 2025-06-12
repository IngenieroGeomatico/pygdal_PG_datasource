import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.Imp_Capas import ProbarGDAL_OGR, leerCapaRaster
from lib.Exp_Capas import escribirCapaRaster

# ProbarGDAL_OGR()


url=[
    "https://cdn.proj.org/es_ign_egm08-rednap.tif"
    "https://wms-potencial-solar.idee.es/potencial-solar"
    "https://www.ign.es/wms-inspire/ign-base",
    "https://servicios.idee.es/wmts/mdt",
    "https://tms-pnoa-ma.idee.es/1.0.0/pnoa-ma/{z}/{x}/{-y}.jpeg"
    ]



# Comienzo proceso Lectura - Cosas - Exportar
banda = None
EPSG_Entrada = 3857
inDataSource= leerCapaRaster(url[0], banda, EPSG_Entrada)

print(inDataSource)


# capa = outDataSource.GetLayerByIndex(0).GetName()   
# lyr = outDataSource.GetLayer(capa)
# for feat in lyr:
#     print(feat.ExportToJson()[0:50])


EPSG_Salida = 25830
out_format = 'GTiff'
WLD =True
outDataSource= escribirCapaRaster(inDataSource, EPSG_Salida,out_format,WLD)

print(outDataSource)

# capa = outDataSource.GetLayerByIndex(0).GetName()   
# lyr = outDataSource.GetLayer(capa)
# print(lyr.ExportToJson())
# for feat in lyr:
#     print(feat.ExportToJson()[0:50])


