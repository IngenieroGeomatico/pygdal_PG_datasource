# Documentación de referencia: 
# https://pcjericks.github.io/py-gdalogr-cookbook/index.html

import sys
# e intenta importar GDAL/OGR
try:
    from osgeo import ogr, osr, gdal
except:
    sys.exit('ERROR: cannot find GDAL/OGR modules')


def ProbarGDAL_OGR():
    # Se comprueba la versión
    version_num = int(gdal.VersionInfo('VERSION_NUM'))

    print('Versión de GDAL/OGR: ', version_num)
    print('----------')
    print(' ')
    if version_num < 1100000:
        sys.exit('ERROR: Python bindings of GDAL 1.10 or later required')

    # Listar drivers Vectoriales
    cnt = ogr.GetDriverCount()
    formatsList = []  # Empty List

    for i in range(cnt):
        driver = ogr.GetDriver(i)
        driverName = driver.GetName()
        if not driverName in formatsList:
            formatsList.append(driverName)

    formatsList.sort() # Sorting the messy list of ogr drivers

    print(' ')
    print('----------')
    print('Drivers vectoriales')
    print('----------')
    print(' ')
    for i in formatsList:
        print(i)

    
    # Listar drivers Ráster
    cnt = gdal.GetDriverCount()
    formatsList = []  # Empty List

    for i in range(cnt):
        driver = gdal.GetDriver(i)
        driverName = driver.LongName
        # driverName = driver.ShortName
        if not driverName in formatsList:
            formatsList.append(driverName)

    formatsList.sort() # Sorting the messy list of ogr drivers

    print(' ')
    print('----------')
    print('DTodos los Drivers')
    print('----------')
    print(' ')
    for i in formatsList:
        print(i)
    print(' ')


    # Se habilitan las excepciones para tener más control
    gdal.UseExceptions()

    # Se intenta abrir un archivo
    ds = gdal.Open('test.tif')


    def gdal_error_handler(err_class, err_num, err_msg):
        errtype = {
                gdal.CE_None:'None',
                gdal.CE_Debug:'Debug',
                gdal.CE_Warning:'Warning',
                gdal.CE_Failure:'Failure',
                gdal.CE_Fatal:'Fatal'
        }
        err_msg = err_msg.replace('\n',' ')
        err_class = errtype.get(err_class, 'None')
        print( 'Error Number: %s' % (err_num))
        print( 'Error Type: %s' % (err_class))
        print( 'Error Message: %s' % (err_msg))

    # install error handler
    gdal.PushErrorHandler(gdal_error_handler)

    # Raise a dummy error
    gdal.Error(1, 2, 'test error')

    #uninstall error handler
    gdal.PopErrorHandler()

    gdal.DontUseExceptions()

def leerCapaVectorial(dato, capa = None, EPSG_Entrada = None , AllLayers = False):
    ogr.UseExceptions()

    if EPSG_Entrada != None:
        if "EPSG" in str(EPSG_Entrada):
            EPSG_Entrada = EPSG_Entrada.split(":")[1]

    if 'http' in dato.lower() and not 'mvt:' in dato.lower():
        dato = "/vsicurl/"+dato

    if 'http' in dato.lower() and 'mvt:' in dato.lower():
        pass

    if 'zip' in dato.lower():
        dato = "/vsizip/"+dato

    try:
        geom = ogr.CreateGeometryFromWkt(dato)
        tipoEntrada = 'wkt'
    except:
        tipoEntrada = 'ogr'


    if tipoEntrada == 'ogr':
        print(dato)
        inDataSource = ogr.Open(dato)
        # gdal.OpenEx()  
        # https://gdal.org/en/stable/api/python/raster_api.html#osgeo.gdal.OpenEx
        # Abrir así si se necesita leer un archivo de forma más genérica

        if AllLayers == True and capa == None:
            return inDataSource

        if capa == None: 
            capa = inDataSource.GetLayerByIndex(0).GetName()
        
        lyr = inDataSource.GetLayer(capa)
        
        # for feat in lyr:
        #     geom = feat.GetGeometryRef()
        #     print(geom.ExportToWkt()[0:50])
        # print('--------------------')

        #create an output datasource in memory
        outdriver=ogr.GetDriverByName('MEMORY')
        outDataSource=outdriver.CreateDataSource(capa)

        #copy a layer to memory
        outLayer=outDataSource.CopyLayer(inDataSource.GetLayer(capa),capa,['OVERWRITE=YES'])

        # for feat in outLayer:
        #     print(feat.ExportToJson())

        return outDataSource

    elif tipoEntrada == 'wkt':

        if EPSG_Entrada == None:
            raise('Falta EPSG de entrada')
        
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(EPSG_Entrada)

        outDriver=ogr.GetDriverByName('MEMORY')
        outDataSource = outDriver.CreateDataSource('memData')
        outLayer = outDataSource.CreateLayer("tmp")

        # Add an ID field
        idField = ogr.FieldDefn("id", ogr.OFTInteger)
        outLayer.CreateField(idField)

        # Create the feature and set values
        featureDefn = outLayer.GetLayerDefn()
        feature = ogr.Feature(featureDefn)
        feature.SetGeometry(geom)
        feature.SetField("id", ogr.OFTInteger)
        outLayer.CreateFeature(feature)

        # for feat in outLayer:
        #     print(feat.ExportToJson())
        
        return outDataSource

    else:
        raise('Valor de entrada no permitido')
    
def leerCapaRaster(dato, banda = None, EPSG_Entrada = None):
    gdal.UseExceptions()

    if EPSG_Entrada != None:
        if "EPSG" in str(EPSG_Entrada):
            EPSG_Entrada = EPSG_Entrada.split(":")[1]

    if 'http' in dato.lower():
        dato = "/vsicurl/"+dato

    if 'zip' in dato.lower():
        dato = "/vsizip/"+dato

    inDataSource = gdal.Open(dato)
    if inDataSource is None:
        raise RuntimeError(f"No se pudo abrir el archivo ráster: {dato}")

    return inDataSource

