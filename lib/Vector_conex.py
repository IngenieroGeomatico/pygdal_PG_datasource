# Documentación de referencia: 
# https://pcjericks.github.io/py-gdalogr-cookbook/index.html

import os
import sys
import json
import zipfile

# e intenta importar GDAL/OGR
try:
    from osgeo import ogr, osr, gdal
except:
    sys.exit('ERROR: cannot find GDAL/OGR modules')
    
class FuenteDatosVector:
    """
    Clase para gestionar la lectura, consulta y exportación de datos vectoriales usando GDAL/OGR.

    
    Atributos:
    ----------
    dato : str
        Ruta, URL o WKT de la fuente de datos vectorial.
    datasource : ogr.DataSource
        Objeto datasource de OGR tras la lectura.
    multiLayers : bool
        Indica si el datasource contiene varias capas.
    """

    @staticmethod
    def probar_gdal_ogr():
        """
        Comprueba la instalación de GDAL/OGR y muestra los drivers vectoriales y ráster disponibles.
        Útil para diagnóstico del entorno.
        """
        version_num = int(gdal.VersionInfo('VERSION_NUM'))

        print('Versión de GDAL/OGR: ', version_num)
        print('----------')
        print(' ')
        if version_num < 1100000:
            sys.exit('ERROR: Python bindings of GDAL 1.10 or later required')

        # Listar drivers Vectoriales
        cnt = ogr.GetDriverCount()
        formatsList = []

        for i in range(cnt):
            driver = ogr.GetDriver(i)
            driverName = driver.GetName()
            if driverName not in formatsList:
                formatsList.append(driverName)

        formatsList.sort()

        print(' ')
        print('----------')
        print('Drivers vectoriales')
        print('----------')
        print(' ')
        for i in formatsList:
            print(i)

        # Listar drivers Ráster
        cnt = gdal.GetDriverCount()
        formatsList = []

        for i in range(cnt):
            driver = gdal.GetDriver(i)
            driverName = driver.LongName
            if driverName not in formatsList:
                formatsList.append(driverName)

        formatsList.sort()

        print(' ')
        print('----------')
        print('DTodos los Drivers')
        print('----------')
        print(' ')
        for i in formatsList:
            print(i)
        print(' ')

        gdal.UseExceptions()

        def gdal_error_handler(err_class, err_num, err_msg):
            errtype = {
                gdal.CE_None: 'None',
                gdal.CE_Debug: 'Debug',
                gdal.CE_Warning: 'Warning',
                gdal.CE_Failure: 'Failure',
                gdal.CE_Fatal: 'Fatal'
            }
            err_msg = err_msg.replace('\n', ' ')
            err_class = errtype.get(err_class, 'None')
            print('Error Number: %s' % (err_num))
            print('Error Type: %s' % (err_class))
            print('Error Message: %s' % (err_msg))

        gdal.PushErrorHandler(gdal_error_handler)
        gdal.Error(1, 2, 'test error')
        gdal.PopErrorHandler()
        gdal.DontUseExceptions()

    def __init__(self, dato):
        """
        Inicializa la clase con la ruta, URL o WKT de la fuente de datos vectorial.

        Parámetros
        ----------
        dato : str
            Ruta, URL o WKT de la fuente de datos vectorial.
        """

        self.dato = dato
        self.datasource = None
        self.multiLayers = False

    def leer(self, capa=None, EPSG_Entrada=None, AllLayers=False):
        """
        Lee la fuente de datos vectorial y la carga en memoria.

        Parámetros
        ----------
        capa : str, opcional
            Nombre de la capa a leer (por defecto, la primera).
        EPSG_Entrada : int o str, opcional
            Código EPSG del sistema de referencia de entrada.
        AllLayers : bool, opcional
            Si es True, carga todas las capas.

        Retorna
        -------
        ogr.DataSource
            Objeto datasource de OGR con la capa leída.
        """

        ogr.UseExceptions()

        if EPSG_Entrada != None:
            if "EPSG" in str(EPSG_Entrada):
                EPSG_Entrada = EPSG_Entrada.split(":")[1]

        dato = self.dato
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
            # print(dato)
            inDataSource = ogr.Open(dato)
            # gdal.OpenEx()  
            # https://gdal.org/en/stable/api/python/raster_api.html#osgeo.gdal.OpenEx
            # Abrir así si se necesita leer un archivo de forma más genérica

            if AllLayers == True and capa == None:
                self.datasource = inDataSource
                self.multiLayers = True
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
            self.datasource = outDataSource
            self.multiLayers = False
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
            self.datasource = outDataSource
            self.multiLayers = False
            return outDataSource

        else:
            raise('Valor de entrada no permitido')  

    def exportar(self, EPSG_Salida=None, outputFormat='application/json'):
        """
        Exporta la capa vectorial a un formato especificado (GeoJSON, Shapefile, etc).

        Parámetros
        ----------
        EPSG_Salida : int o str, opcional
            Código EPSG del sistema de referencia de salida.
        outputFormat : str, opcional
            Formato de salida (por ejemplo, 'application/json', 'GeoJSON', 'ESRI Shapefile').

        Retorna
        -------
        str o bytes
            GeoJSON como string o archivo exportado como blob.
        """
        
        ogr.UseExceptions()

        if self.datasource is None:
            raise Exception("Primero debes llamar a leer()")

        dato = self.datasource

        if outputFormat == 'application/json':
            capa = dato.GetLayerByIndex(0)

            srs_original = capa.GetSpatialRef()
            srs = osr.SpatialReference()
            srs.ImportFromEPSG(4326)

            
            geojson = {
                "type": "FeatureCollection",
                "features": []
            }

            if srs != srs_original:
                transform = osr.CoordinateTransformation(srs_original, srs)
                for feat in capa:
                    geom = feat.GetGeometryRef()
                    geom.Transform(transform)  
                    feat.SetGeometry(geom)
                    geojson["features"].append(feat.ExportToJson(as_object=True))

            else:
                for feat in capa:
                    # print(feat.ExportToJson())
                    geojson["features"].append(feat.ExportToJson(as_object=True))

            return json.dumps(geojson)
        
        else:
            outPath ="./tmp/"
            fileName = os.path.splitext(os.path.basename(dato.GetDescription()))[0]
            if "FeatureCollection" and "features" in fileName:
                fileName = "objGeoJSON"
            outputPath = outPath + fileName
            outputDir = os.path.dirname(outputPath)

            if not os.path.exists(outputDir):
                os.makedirs(outputDir)

            # Validar el formato de salida
            driver = ogr.GetDriverByName(outputFormat)
            if driver is None:
                raise RuntimeError(f"El formato de salida '{outputFormat}' no es compatible con GDAL.")

            # Obtener la extensión del driver
            metadata = driver.GetMetadata()
            extension = metadata.get('DMD_EXTENSION', None)

            if extension is None:
                extension = metadata.get('DMD_EXTENSIONS', None).split()[-2] if '.' in metadata.get('DMD_EXTENSIONS', '') else metadata.get('DMD_EXTENSIONS', '').split()[-1]

            if extension is None:
                raise RuntimeError(f"El driver '{ogr.GetDriverByName(outputFormat)}' no tiene una extensión predeterminada.")
            
            outputPath += "." + extension
            orioutputPath = outputPath
            filesArray = []

            # Crear el archivo de salida
            outDataSource = driver.CreateDataSource(outputPath)
            if outDataSource is None:
                raise RuntimeError(f"No se pudo crear el archivo de salida en '{outDataSource}'.")
            
            # Iterar sobre todas las capas del dataset
            deleteFileifError = False
            multiFiles = False
            for i in range(dato.GetLayerCount()):
                capa = dato.GetLayerByIndex(i)
                nombreCapa = capa.GetName()

                # Crear una nueva capa en el archivo de salida
                srs = osr.SpatialReference()
                # TODO: crear una fuente de datos por capa si da error la exportación
                srs.ImportFromEPSG(int(EPSG_Salida))
                try:
                    outLayer = outDataSource.CreateLayer(nombreCapa, srs = srs, geom_type=capa.GetGeomType())
                    
                    if multiFiles == False:
                        base_name = os.path.splitext(os.path.basename(fileName))[0]

                        # Buscar todos los archivos en outPath que contengan el mismo nombre base
                        n = 0
                        for file_name in os.listdir(outPath):
                            if file_name.startswith(base_name): 
                                n += 1
                            if n > 1:
                                # Si hay más de un archivo con el mismo nombre base, se considera que es un archivo múltiple
                                multiFiles = True
                                for file_name in os.listdir(outPath):
                                    full_path = os.path.join(outPath, file_name)
                                    new_name = file_name.replace(base_name, nombreCapa)  # Reemplazar base_name por nombreCapa
                                    new_path = os.path.join(outPath, new_name)
                                    os.rename(full_path, new_path) 
                                break

                    if multiFiles:
                        for file_name in os.listdir(outPath):
                            if file_name.startswith(nombreCapa): 
                                filesArray.append(os.path.join(outPath, file_name))
                            


                except RuntimeError as e:
                    deleteFileifError = True
                    outputPath = orioutputPath.replace('.' + extension, f'_{nombreCapa}.' + extension)
                    outDataSource = driver.CreateDataSource(outputPath)
                    outLayer = outDataSource.CreateLayer(nombreCapa, srs = srs, geom_type=capa.GetGeomType())
                    filesArray.append(outputPath)


                # Copiar los campos de la capa original
                layerDefn = capa.GetLayerDefn()
                for j in range(layerDefn.GetFieldCount()):
                    fieldDefn = layerDefn.GetFieldDefn(j)
                    outLayer.CreateField(fieldDefn)

                srs_original = capa.GetSpatialRef()

                if EPSG_Salida != None:
                    if "EPSG" in str(EPSG_Salida):
                        EPSG_Salida = EPSG_Salida.split(":")[1]
                    
                    if srs != srs_original:
                        transform = osr.CoordinateTransformation(srs_original, srs)

                        # Transformar y copiar las geometrías
                        for feature in capa:
                            geom = feature.GetGeometryRef()
                            if transform:
                                geom.Transform(transform)  # Reproyectar la geometría

                            outFeature = ogr.Feature(outLayer.GetLayerDefn())
                            outFeature.SetGeometry(geom)
                            for j in range(layerDefn.GetFieldCount()):
                                outFeature.SetField(layerDefn.GetFieldDefn(j).GetNameRef(), feature.GetField(j))
                            outLayer.CreateFeature(outFeature)
                            outFeature = None

            outDataSource = None
            if deleteFileifError or multiFiles:
                
                if multiFiles:
                    base_name = os.path.splitext(os.path.basename(orioutputPath))[0]

                    for file_name in os.listdir(outPath):
                        if file_name.startswith(base_name): 
                            full_path = os.path.join(outPath, file_name)
                            os.remove(full_path)
                else:
                    os.remove(orioutputPath)


                # Crear un archivo ZIP con los archivos exportados
                zip_output_path = orioutputPath.replace('.' + extension, '.zip')
                try:
                    with zipfile.ZipFile(zip_output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                        for file_path in filesArray:
                            # Obtener el nombre base sin la extensión
                            base_name = os.path.splitext(os.path.basename(file_path))[0]
        
                            # Buscar todos los archivos en outPath que contengan el mismo nombre base
                            for file_name in os.listdir(outPath):
                                if ".zip" in file_name:
                                    continue
                                if file_name.startswith(base_name):  # Verificar si el archivo coincide con el nombre base
                                    full_path = os.path.join(outPath, file_name)
                                    zipf.write(full_path, os.path.basename(full_path))  # Agregar al ZIP
                                    os.remove(full_path)  # Eliminar el archivo después de añadirlo
                    
                    print(f"Archivo ZIP creado exitosamente en: {zip_output_path}")
                    outputPath = zip_output_path
                except Exception as e:
                    raise RuntimeError(f"Error al crear el archivo ZIP: {e}")

            try:
                with open(outputPath, 'rb') as archivo:
                    blob = archivo.read()
                print(f"Archivo leído exitosamente desde: {outputPath}")
                return blob
            
            except Exception as e:
                raise RuntimeError(f"Error al escribir el archivo ráster: {e}")
            
            finally:
                # Cerrar el dataset de salida
                outDataset = None

    def obtener_capas(self):
        """
        Devuelve una lista con los nombres de todas las capas presentes en el datasource.

        Retorna
        -------
        list of str
            Lista con los nombres de las capas del datasource.

        Excepciones
        -----------
        Exception
            Si no se ha leído ningún datasource previamente.
        """
        if self.datasource is None:
            raise Exception("Primero debes llamar a leer()")

        capas = []
        for i in range(self.datasource.GetLayerCount()):
            layer = self.datasource.GetLayerByIndex(i)
            capas.append(layer.GetName())
        return capas

    def obtener_atributos(self, capa=None):
        """
        Devuelve los atributos y sus tipos de una capa o de todas las capas.

        Parámetros
        ----------
        capa : str, opcional
            Nombre de la capa (por defecto, todas).

        Retorna
        -------
        dict
            Si capa es None: {nombre_capa: {campo: tipo, ...}, ...}
            Si capa se indica: {campo: tipo, ...}
        """
        if self.datasource is None:
            raise Exception("Primero debes llamar a leer()")

        def campos_dict(layer):
            layer_defn = layer.GetLayerDefn()
            return {
                layer_defn.GetFieldDefn(i).GetName(): layer_defn.GetFieldDefn(i).GetFieldTypeName(layer_defn.GetFieldDefn(i).GetType())
                for i in range(layer_defn.GetFieldCount())
            }

        if capa:
            layer = self.datasource.GetLayer(capa)
            if layer is None:
                raise Exception(f"No existe la capa '{capa}'")
            return campos_dict(layer)
        else:
            result = {}
            for i in range(self.datasource.GetLayerCount()):
                lyr = self.datasource.GetLayerByIndex(i)
                result[lyr.GetName()] = campos_dict(lyr)
            return result