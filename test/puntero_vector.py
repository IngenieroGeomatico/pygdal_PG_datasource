import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.Vector_conex import FuenteDatosVector
# ProbarGDAL_OGR()
url=[
    "http://geostematicos-sigc.juntadeandalucia.es/geoserver/tematicos/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=tematicos:Provincias&maxFeatures=50&outputFormat=application/json",

    "https://www.juntadeandalucia.es/institutodeestadisticaycartografia/dega/sites/default/files/datos/094-dera-1-relieve.zip",

    "POINT (1120351.5712494177 741921.4223245403)",

    'POLYGON ((756940.8564184426 4521820.812141684, 755700.7757705624 4519670.898155319, 753220.6144748018 4519670.898155319, 751980.5338269215 4521820.812141684, 753220.6144748018 4523970.726128049, 755700.7757705624 4523970.726128049, 756940.8564184426 4521820.812141684))',

    """
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {},
      "geometry": {
        "coordinates": [
          [
            -10.761695260635861,
            40.11164756110395
          ],
          [
            2.9492422393651907,
            39.977078912732225
          ],
          [
            -13.04685151063569,
            45.39841223726671
          ],
          [
            4.003929739364821,
            44.27663279278741
          ]
        ],
        "type": "LineString"
      }
    },
    {
      "type": "Feature",
      "properties": {},
      "geometry": {
        "coordinates": [
          [
            -12.167945260635406,
            35.817769576942766
          ],
          [
            -17.265601510635378,
            52.106472180124456
          ],
          [
            5.234398489364935,
            45.27484861557224
          ]
        ],
        "type": "LineString"
      }
    }
  ]
}
""",

    "POLYGON ((-10.761695260635861 40.11164756110395, 2.9492422393651907 39.977078912732225, -13.04685151063569 45.39841223726671, 4.003929739364821 44.27663279278741, -10.761695260635861 40.11164756110395))",

    "MVT:https://vt-btn.idee.es/1.0.0/btn/tile/1",
    
]

fuenteDatos = url[1]

# Comienzo proceso Lectura - Cosas - Exportar
# FuenteDatosVector.probar_gdal_ogr()

fuenteDatosObj = FuenteDatosVector(fuenteDatos)
fuenteDatos = fuenteDatosObj.leer()

capa = fuenteDatos.GetLayerByIndex(0).GetName()   
lyr = fuenteDatos.GetLayer(capa)
print("Número de objetos geográficos:", lyr.GetFeatureCount())

lyr.ResetReading()
if lyr is None:
    print("No se encontró la capa con ese nombre.")

# lyr.ResetReading()
# for feat in lyr:
#     print(feat.ExportToJson()[0:50])

print()

EPSG_Salida = 3857
out_format = 'application/json'
outDataSource = fuenteDatosObj.exportar(EPSG_Salida=EPSG_Salida, outputFormat=out_format)
print(outDataSource)


