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
    
class FuenteDatosRaster:

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
        self.dato = dato
        self.datasource = None

    def leer(self, banda = None, EPSG_Entrada = None):
        gdal.UseExceptions()

        if EPSG_Entrada != None:
            if "EPSG" in str(EPSG_Entrada):
                EPSG_Entrada = EPSG_Entrada.split(":")[1]

        dato = self.dato
        if 'http' in dato.lower():
            dato = "/vsicurl/"+dato

        if 'zip' in dato.lower():
            dato = "/vsizip/"+dato

        inDataSource = gdal.Open(dato)
        if inDataSource is None:
            raise RuntimeError(f"No se pudo abrir el archivo ráster: {dato}")
        
        self.datasource = inDataSource
        return inDataSource

    def exportar(self, EPSG_Salida = None, outputFormat = 'GTiff', WLD = False):
        gdal.UseExceptions()

        if self.datasource is None:
            raise Exception("Primero debes llamar a leer()")

        dato = self.datasource

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
        dato.SetMetadata({'CREATED_BY': 'GDAL Python'})
        dato.FlushCache()
        dato = None  # Cerrar el dataset para que se escriba el PAM
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