# Documentación de referencia: 
# https://pcjericks.github.io/py-gdalogr-cookbook/index.html
# https://gdal.org/en/stable/api/python/index.html

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

    def leer(self, capa=None, EPSG_Entrada=None, datasetCompleto=False):
        """
        Lee la fuente de datos vectorial y la carga en memoria.

        Parámetros
        ----------
        capa : str, opcional
            Nombre de la capa a leer (por defecto, la primera).
        EPSG_Entrada : int o str, opcional
            Código EPSG del sistema de referencia de entrada.
        datasetCompleto : bool, opcional
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

            if datasetCompleto == True and capa == None:
                self.datasource = inDataSource
                self.multiLayers = True
                return inDataSource

            if capa == None: 
                capa = inDataSource.GetLayerByIndex(0).GetName()
            else:
                try:
                    idx = int(capa)
                    capa = inDataSource.GetLayerByIndex(idx).GetName()
                except (ValueError, TypeError):
                    capa = inDataSource.GetLayer(capa).GetName()
                if capa is None:
                    raise Exception(f"No existe la capa '{capa}'")
                
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

            if EPSG_Entrada is None:
                raise Exception('Falta EPSG de entrada')

            srs = osr.SpatialReference()

            if isinstance(EPSG_Entrada, str):
                EPSG_Entrada = EPSG_Entrada.replace(" ", "")
                if EPSG_Entrada.startswith("EPSG:"):
                    EPSG_Entrada = int(EPSG_Entrada.split(":")[1])
                else:
                    EPSG_Entrada = int(EPSG_Entrada)

            srs.ImportFromEPSG(EPSG_Entrada)

            outDriver = ogr.GetDriverByName('MEMORY')
            outDataSource = outDriver.CreateDataSource('memData')
            outLayer = outDataSource.CreateLayer("tmp", srs=srs)

            # Add an ID field
            idField = ogr.FieldDefn("id", ogr.OFTInteger)
            outLayer.CreateField(idField)

            featureDefn = outLayer.GetLayerDefn()
            feature = ogr.Feature(featureDefn)
            feature.SetGeometry(geom)
            feature.SetField("id", 1)  # aquí asignamos un valor entero
            outLayer.CreateFeature(feature)

            self.datasource = outDataSource
            self.multiLayers = False
            return outDataSource

        else:
            raise('Valor de entrada no permitido')  

    def exportar(self, capa = None, EPSG_Salida=None, outputFormat='application/json', ID=None):
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

        if outputFormat == 'application/json'  or outputFormat == 'json':
            # Seleccionar la capa de entrada
            capa = self.datasource.GetLayer(self.obtener_nombreCapa(capa))
        
            srs_original = capa.GetSpatialRef()
            srs = osr.SpatialReference()
            srs.ImportFromEPSG(4326)

            layer_defn = capa.GetLayerDefn()

            # Comprobar si existe
            if ID:
                idx = layer_defn.GetFieldIndex(ID)
                if idx == -1:
                    ID = None
            
            geojson = {
                "type": "FeatureCollection",
                "features": []
            }


            if (not srs.IsSame(srs_original) and 
                srs_original.GetAttrValue("AUTHORITY", 1)!=srs.GetAttrValue("AUTHORITY", 1)):

                transform = osr.CoordinateTransformation(srs_original, srs)
                for feat in capa:
                    geom = feat.GetGeometryRef()
                    if geom is not None:
                        geom.Transform(transform)
                    feat.SetGeometry(geom)
                    obj = feat.ExportToJson(as_object=True)
                    if ID:
                        obj['id'] = feat.GetField(ID)
                    geojson["features"].append(obj)

            else:
                for feat in capa:
                    obj = feat.ExportToJson(as_object=True)
                    if ID:
                        obj['id'] = feat.GetField(ID)
                    geojson["features"].append(obj)

            return geojson
        
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
                srs.ImportFromEPSG(int(EPSG_Salida))

                # TODO: crear una fuente de datos por capa si da error la exportación

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
                                if geom is not None:
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

    def ejecutar_sql(self, sql, capa, dialect='OGRSQL'):
        """
        Ejecuta una sentencia SQL sobre el datasource y retorna el resultado como un nuevo datasource en memoria.

        Documentación de referencia: https://gdal.org/en/stable/user/ogr_sql_dialect.html

        Parámetros
        ----------
        sql : str
            Sentencia SQL a ejecutar (por ejemplo, 'SELECT * FROM capa WHERE ...').
        capa : str
            Nombre de la capa donde se guardará el resultado de la consulta.
        dialect : str, opcional
            Dialecto SQL a usar ('OGRSQL' por defecto, también puede ser 'SQLITE').

        Retorna
        -------
        ogr.DataSource
            Nuevo datasource en memoria con el resultado de la consulta.

        Excepciones
        -----------
        Exception
            Si no se ha leído ningún datasource previamente, la consulta falla.
        """
        if self.datasource is None:
            raise Exception("Primero debes llamar a leer()")

        # Ejecutar la consulta SQL
        resultado = self.datasource.ExecuteSQL(sql, dialect=dialect)

        self.datasource.CopyLayer(resultado, capa)
        self.datasource.ReleaseResultSet(resultado)
        
        # Si la capa existe, elimínala
        if self.datasource.GetLayerByName(capa) and self.obtener_capas().count(capa) > 1:
            self.datasource.DeleteLayer(capa)
            self.datasource.SyncToDisk()

        return self.datasource.GetLayerByName(capa)
    
    def MRE_datos(self, capaEntrada=None, capaSalida=None, MRE=[-180, -90, 180, 90], EPSG_MRE=4326):
        """
        Aplica un filtro espacial (bbox) a una capa y guarda la capa filtrada en el dataset con el nombre capaSalida.

        Parámetros
        ----------
        capaEntrada : str o int
            Nombre o índice de la capa a filtrar.
        capaSalida : str
            Nombre de la capa filtrada en el dataset.
        MRE : list[float]
            Bounding box [minx, miny, maxx, maxy].
        EPSG_MRE : int
            EPSG del bbox.

        Retorna
        -------
        ogr.Layer
            La nueva capa filtrada.
        """
        if self.datasource is None:
            raise Exception("Primero debes llamar a leer()")

        tmpLayer = "_tmpMRE"
        # Seleccionar la capa de entrada
        layer = self.datasource.GetLayer(self.obtener_nombreCapa(capaEntrada))
        
        # Obtener el SRS de la capa
        srs_capa = layer.GetSpatialRef()
        if srs_capa is None:
            raise Exception("La capa no tiene sistema de referencia espacial definido.")

        srs_bbox = osr.SpatialReference()
        if isinstance(EPSG_MRE, str):
            if EPSG_MRE.startswith("EPSG:"):
                EPSG_MRE = int(EPSG_MRE.split(":")[1])
            else:
                EPSG_MRE = int(EPSG_MRE)
        srs_bbox.ImportFromEPSG(EPSG_MRE)

        # Crear el polígono del bbox en EPSG_MRE    
        if srs_bbox.EPSGTreatsAsLatLong() or srs_bbox.EPSGTreatsAsNorthingEasting():
            miny, minx, maxy, maxx = [float(b) for b in MRE]
        else:
            minx, miny, maxx, maxy = [float(b) for b in MRE]

        pol_wkt = f"POLYGON (({minx} {miny},{minx} {maxy},{maxx} {maxy},{maxx} {miny},{minx} {miny}))"
        
        polygon = ogr.CreateGeometryFromWkt(pol_wkt,srs_bbox)
        
        # Asignar SRS solo si el polígono no lo tiene
        polygon.AssignSpatialReference(srs_bbox)

        # Transformar si es necesario
        if not srs_capa.IsSame(srs_bbox):
            transform = osr.CoordinateTransformation(srs_bbox, srs_capa)
            polygon.Transform(transform)

        layer.SetSpatialFilter(polygon)

        if self.datasource.GetLayerByName(capaSalida) and capaSalida != capaEntrada:
            self.datasource.DeleteLayer(capaSalida)
            self.datasource.SyncToDisk()
        
        elif capaSalida is None:
            capaSalida = capaEntrada + tmpLayer
        
        geom_type = layer.GetGeomType() or ogr.wkbUnknown
        layer_salida = self.datasource.CreateLayer(capaSalida, srs_capa, geom_type)
        if layer_salida is None:
            raise RuntimeError(f"No se pudo crear la capa '{capaSalida}'")

        layer_defn = layer.GetLayerDefn()
        for i in range(layer_defn.GetFieldCount()):
            field_defn = layer_defn.GetFieldDefn(i)
            layer_salida.CreateField(field_defn)

        layer_defn_salida = layer_salida.GetLayerDefn()
        for feature in layer:
            new_feature = ogr.Feature(layer_defn_salida)
            new_feature.SetFrom(feature)
            layer_salida.CreateFeature(new_feature)
            new_feature = None

        layer.SetSpatialFilter(None)

        if tmpLayer in capaSalida:
            capaSalidaReal = capaSalida.replace(tmpLayer, "")
            # Si la capa existe, elimínala
            if self.datasource.GetLayerByName(capaSalidaReal):
                self.datasource.DeleteLayer(capaSalidaReal)
                self.datasource.SyncToDisk()
            self.datasource.CopyLayer(layer_salida, capaSalidaReal)
            self.datasource.DeleteLayer(capaSalida)
            self.datasource.SyncToDisk()
            capaSalida = capaSalidaReal

        layer_salida = None

        return self.datasource.GetLayerByName(capaSalida)

    def obtener_atributos(self, capa=None):
        """
        Devuelve los atributos y sus tipos de una capa o de todas las capas en formato:
        {
            'nombre_capa': {
                'nombre_propiedad': {'type': 'string'},
                ...
            },
            ...
        }
        Si se indica capa, devuelve solo el diccionario de esa capa.
        """
        if self.datasource is None:
            raise Exception("Primero debes llamar a leer()")

        def atributos_layer(layer):
            layer_defn = layer.GetLayerDefn()
            atributos = {}
            for i in range(layer_defn.GetFieldCount()):
                field_defn = layer_defn.GetFieldDefn(i)
                field_name = field_defn.GetName()
                field_type = field_defn.GetFieldTypeName(field_defn.GetType()).lower()
                # Mapear tipos OGR a tipos JSON simples
                if field_type in ['integer', 'integer64']:
                    tipo = 'integer'
                elif field_type in ['real', 'float', 'double']:
                    tipo = 'number'
                else:
                    tipo = 'string'
                atributos[field_name] = {'type': tipo}
            return atributos

        if capa:
            layer = self.datasource.GetLayer(capa)
            if layer is None:
                raise Exception(f"No existe la capa '{capa}'")
            return atributos_layer(layer)
        else:
            resultado = {}
            for i in range(self.datasource.GetLayerCount()):
                lyr = self.datasource.GetLayerByIndex(i)
                resultado[lyr.GetName()] = atributos_layer(lyr)
            return resultado

    def obtener_nombreCapa(self, capa=None):

        if capa is None:
            layer = self.datasource.GetLayerByIndex(0)
        else:
            try:
                idx = int(capa)
                layer = self.datasource.GetLayerByIndex(idx)
            except (ValueError, TypeError):
                layer = self.datasource.GetLayer(capa)
            if layer is None:
                raise Exception(f"No existe la capa '{capa}'")
            
        return layer.GetName()

    def obtener_indice_capa(self, nombre_capa):
        """
        Devuelve el índice de la capa dado su nombre.
        Lanza una excepción si no existe.
        """
        for i in range(self.datasource.GetLayerCount()):
            layer = self.datasource.GetLayerByIndex(i)
            if layer.GetName() == nombre_capa:
                return i
        raise Exception(f"No existe la capa '{nombre_capa}'")

    def borrar_geometria(self, capa=None):
        layer = self.datasource.GetLayer(self.obtener_nombreCapa(capa))
        for feature in layer:
            feature.SetGeometry(None)
            layer.SetFeature(feature)

        return layer

    def crear_ID(self, capa=None, nombreCampo='ID_OGR'):
        """
        Crea una ID para una capa y le asigna un valor secuencial.
        
        :param capa: nombre o identificador de la capa
        :param nombreCampo: nombre del campo ID
        :return: capa con el campo ID creado
        """
        layer = self.datasource.GetLayer(self.obtener_nombreCapa(capa))
        
        id_field = ogr.FieldDefn(nombreCampo, ogr.OFTInteger)
        layer.CreateField(id_field)

        # Asigna valores secuenciales
        for i, feature in enumerate(layer):
            feature.SetField(nombreCampo, i)
            layer.SetFeature(feature)  # guarda el cambio
            feature = None  # limpia

        layer.SyncToDisk()  # asegura que se guarden los cambios

        return layer
    
    def obtener_objeto_porID(self, capaEntrada=None, capaSalida=None, ID='ID_OGR', valorID=0):
        """
        Obtiene un objeto por su ID en una capa específica.

        :param capaEntrada: nombre o índice de la capa
        :param capaSalida: nombre de la capa de salida con el resultado
        :param ID: nombre del campo ID a buscar
        :param valorID: valor del ID a buscar
        :return: capa con el objeto encontrado o None si no existe.
        """
        nombre_entrada = self.obtener_nombreCapa(capaEntrada)
        layer = self.datasource.GetLayerByName(nombre_entrada)

        if not layer:
            raise Exception(f"No existe la capa '{capaEntrada}'")

        # Aplicar filtro
        filter_expr = f"{ID} = '{valorID}'" if isinstance(valorID, str) else f"{ID} = {valorID}"
        layer.SetAttributeFilter(filter_expr)

        # Si no se especifica capa de salida o es igual que la de entrada
        overwrite = False
        if capaSalida is None or capaSalida == capaEntrada:
            capaSalida = f"{nombre_entrada}_tmp"
            overwrite = True

        # Crear capa de salida
        srs = layer.GetSpatialRef()
        geom_type = layer.GetGeomType()
        layer_defn = layer.GetLayerDefn()

        # Eliminar si ya existe
        if self.datasource.GetLayerByName(capaSalida):
            self.datasource.DeleteLayer(capaSalida)
            self.datasource.SyncToDisk()

        capa_salida = self.datasource.CreateLayer(capaSalida, srs, geom_type)

        # Copiar campos
        for i in range(layer_defn.GetFieldCount()):
            field_defn = layer_defn.GetFieldDefn(i)
            capa_salida.CreateField(field_defn)

        # Copiar features filtradas
        for feature in layer:
            new_feature = ogr.Feature(capa_salida.GetLayerDefn())
            new_feature.SetFrom(feature)
            capa_salida.CreateFeature(new_feature)
            new_feature = None

        # Restaurar capa de entrada
        layer.SetAttributeFilter(None)

        # Si es sobrescritura, renombrar
        if overwrite:
            self.datasource.DeleteLayer(nombre_entrada)
            self.datasource.CopyLayer(capa_salida, nombre_entrada)
            self.datasource.DeleteLayer(capaSalida)
            self.datasource.SyncToDisk()
            capaSalida = nombre_entrada

        return self.datasource.GetLayerByName(capaSalida)

    def reproyectar_datasource(self, EPSG_salida):
        """
        Reproyecta todas las capas de self.datasource al EPSG_salida.
        Si una capa ya está en ese EPSG, simplemente se copia sin reproyección.
        """
        src_ds = self.datasource
        driver = ogr.GetDriverByName("Memory")
        dst_ds = driver.CreateDataSource("")

        # Crear SRS objetivo
        target_srs = osr.SpatialReference()
        target_srs.ImportFromEPSG(EPSG_salida)

        for i in range(src_ds.GetLayerCount()):
            layer = src_ds.GetLayerByIndex(i)
            source_srs = layer.GetSpatialRef()

            if source_srs is None:
                raise ValueError(f"La capa {i} no tiene definido un sistema de referencia espacial (SRS)")

            # Determinar si necesita transformación
            if (target_srs.IsSame(source_srs) and 
                source_srs.GetAttrValue("AUTHORITY", 1)==target_srs.GetAttrValue("AUTHORITY", 1)):

                transform = None
            else:
                transform = osr.CoordinateTransformation(source_srs, target_srs)
                print(f">>> Reproyectando capa '{layer.GetName()}' de {source_srs.GetAttrValue('AUTHORITY',1)} a {EPSG_salida}")

            # Crear nueva capa
            dst_layer = dst_ds.CreateLayer(layer.GetName(), srs=target_srs, geom_type=layer.GetGeomType())

            # Copiar campos
            layer_defn = layer.GetLayerDefn()
            for j in range(layer_defn.GetFieldCount()):
                dst_layer.CreateField(layer_defn.GetFieldDefn(j))

            dst_defn = dst_layer.GetLayerDefn()

            # Copiar y (si es necesario) transformar geometrías
            for feature in layer:
                geom = feature.GetGeometryRef()
                if geom:
                    geom_clone = geom.Clone()
                    if transform:
                        geom_clone.Transform(transform)

                    new_feat = ogr.Feature(dst_defn)
                    new_feat.SetGeometry(geom_clone)
                    for j in range(layer_defn.GetFieldCount()):
                        new_feat.SetField(j, feature.GetField(j))
                    dst_layer.CreateFeature(new_feat)
                    new_feat = None

            layer.ResetReading()

        # Reemplazar datasource
        self.datasource = dst_ds
        return dst_ds

    def añadir_capa(self, src_capa):
        """
        Añade al DataSource dst_ds una capa basada en src_layer (objeto ogr.Layer).
        Si ya existe una capa con ese nombre en dst_ds, la elimina primero.

        Copia la estructura (campos) y todas las features con sus geometrías.
        """
        dst_ds =  self.datasource
        layer_name = src_capa.GetName()

        # Si ya existe la capa destino, eliminarla
        existing_layer = dst_ds.GetLayerByName(layer_name)
        if existing_layer:
            dst_ds.DeleteLayer(layer_name)

        # Crear nueva capa en dst_ds con el mismo SRS y tipo geométrico que src_capa
        srs = src_capa.GetSpatialRef()
        geom_type = src_capa.GetGeomType()
        dst_layer = dst_ds.CreateLayer(layer_name, srs=srs, geom_type=geom_type)

        # Copiar campos (atributos)
        src_defn = src_capa.GetLayerDefn()
        for i in range(src_defn.GetFieldCount()):
            field_defn = src_defn.GetFieldDefn(i)
            dst_layer.CreateField(field_defn)

        dst_defn = dst_layer.GetLayerDefn()

        # Copiar features (geometría + atributos)
        for feature in src_capa:
            new_feature = ogr.Feature(dst_defn)
            new_feature.SetGeometry(feature.GetGeometryRef())
            for i in range(src_defn.GetFieldCount()):
                new_feature.SetField(i, feature.GetField(i))
            dst_layer.CreateFeature(new_feature)
            new_feature = None

        src_capa.ResetReading()
        return dst_layer

