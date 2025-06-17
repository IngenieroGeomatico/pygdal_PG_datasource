import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.Raster_conex import FuenteDatosRaster

# ProbarGDAL_OGR()


url=[
    "https://cdn.proj.org/es_ign_egm08-rednap.tif",
    "https://wms-potencial-solar.idee.es/potencial-solar",
    "https://www.ign.es/wms-inspire/ign-base",
    "https://servicios.idee.es/wmts/mdt",
    "https://tms-pnoa-ma.idee.es/1.0.0/pnoa-ma/{z}/{x}/{-y}.jpeg"
    ]


fuenteDatos = url[0]

# Comienzo proceso Lectura - Cosas - Exportar
# FuenteDatosVector.probar_gdal_ogr()

banda = None
EPSG_Entrada = 3857

fuenteDatosObj = FuenteDatosRaster(fuenteDatos)
fuenteDatos = fuenteDatosObj.leer(banda, EPSG_Entrada)

print(fuenteDatos)

EPSG_Salida = 25830
out_format = 'GTiff'
WLD =True
outDataSource= fuenteDatosObj.exportar(EPSG_Salida,out_format,WLD)

# print(outDataSource)


