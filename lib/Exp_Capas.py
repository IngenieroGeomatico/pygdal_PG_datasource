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

def escribirCapaVectorial(dato,  EPSG_Salida = None, outputFormat = 'aplication/json'):
    ogr.UseExceptions()

    if outputFormat == 'aplication/json':
        capa = dato.GetLayerByIndex(0)

        geojson = {
            "type": "FeatureCollection",
            "features": []
        }

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
            print(f"Archivo ráster guardado exitosamente en: {outputPath}")
            return blob
        
        except Exception as e:
            raise RuntimeError(f"Error al escribir el archivo ráster: {e}")
        
        finally:
            # Cerrar el dataset de salida
            outDataset = None

def escribirCapaRaster(dato,  EPSG_Salida = None, outputFormat = 'GTiff', WLD = False):
    gdal.UseExceptions()

    outPath ="./tmp/"
    fileName = os.path.splitext(os.path.basename(dato.GetDescription()))[0]
    outputPath = outPath + fileName
    outputDir = os.path.dirname(outputPath)
    if not os.path.exists(outputDir):
        os.makedirs(outputDir)

    # Validar el formato de salida
    driver = gdal.GetDriverByName(outputFormat)
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

    CreateOptionsArray = []
    if WLD:
        CreateOptionsArray=["WORLDFILE=YES"] 

    if EPSG_Salida != None:
        if "EPSG" in str(EPSG_Salida):
            EPSG_Salida = EPSG_Salida.split(":")[1]

        # Crear un sistema de referencia espacial
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(int(EPSG_Salida))


        # Reproyectar el dataset
        warp_options = gdal.WarpOptions( dstSRS=srs.ExportToWkt(),creationOptions=CreateOptionsArray)
    else:
        warp_options = gdal.WarpOptions( creationOptions=CreateOptionsArray)

    dato = gdal.Warp(outputPath, dato, options=warp_options, format=outputFormat)

    filesArray = []
    for file_name in os.listdir(outPath):
        if file_name.startswith(fileName): 
            full_path = os.path.join(outPath, file_name)
            filesArray.append(full_path)

    if len(filesArray) > 1:
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


    # Crear una copia del dataset en el formato de salida
    try:
        with open(outputPath, 'rb') as archivo:
            blob = archivo.read()
        print(f"Archivo ráster guardado exitosamente en: {outputPath}")
        return blob
    
    except Exception as e:
        raise RuntimeError(f"Error al escribir el archivo ráster: {e}")
    
    finally:
        # Cerrar el dataset de salida
        outDataset = None


