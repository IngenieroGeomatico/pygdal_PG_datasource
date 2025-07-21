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
    """
    Clase para gestionar la lectura, consulta y exportación de datos ráster usando GDAL.

    Métodos principales:
    --------------------
    - probar_gdal_ogr(): Comprueba la instalación y muestra los drivers disponibles de GDAL/OGR.
    - leer(): Lee una fuente de datos ráster desde archivo, URL, etc.
    - exportar(): Exporta el ráster a diferentes formatos (GTiff, JPEG, etc).

    Atributos:
    ----------
    dato : str
        Ruta o URL de la fuente de datos ráster.
    datasource : gdal.Dataset
        Objeto dataset de GDAL tras la lectura.
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
        Inicializa la clase con la ruta o URL de la fuente de datos ráster.

        Parámetros
        ----------
        dato : str
            Ruta o URL de la fuente de datos ráster.
        """
        self.dato = dato
        self.datasource = None
        self.multiBand = True

    def leer(self, banda = None, EPSG_Entrada = None, datasetCompleto=True):
        """
        Lee la fuente de datos ráster y la carga en memoria.

        Parámetros
        ----------
        banda : int, opcional
            Número de banda a leer (por defecto, todas).
        EPSG_Entrada : int o str, opcional
            Código EPSG del sistema de referencia de entrada, si la entrada no tiene.

        Retorna
        -------
        gdal.Dataset
            Objeto dataset de GDAL con el ráster leído.
        """
        gdal.UseExceptions()

        if banda:
            datasetCompleto=False
            self.multiBand = False

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

        # Obtener proyección actual
        proj = inDataSource.GetProjection()
        if proj and proj.strip():
            pass
        else:
            # Crear sistema de referencia
            srs = osr.SpatialReference()
            srs.ImportFromEPSG(int(EPSG_Entrada))

            # Asignar proyección
            inDataSource.SetProjection(srs.ExportToWkt())

        if datasetCompleto == True and banda == None:
            self.datasource = inDataSource
            self.multiLayers = True
            return inDataSource
        
        if banda == None: 
            banda = 1
        else:
            try:
                idx = int(banda)
                capa = inDataSource.GetRasterBand(idx)
            except (ValueError, TypeError):
                raise Exception(f"No existe la banda '{banda}'")
            if capa is None:
                raise Exception(f"No existe la banda '{banda}'")

        band_array = capa.ReadAsArray()

        # Crear driver en memoria
        driver = gdal.GetDriverByName('MEM')

        # Crear dataset en memoria con una sola banda
        mem_ds = driver.Create(
            inDataSource.GetDescription(),
            inDataSource.RasterXSize,
            inDataSource.RasterYSize,
            1,  # número de bandas
            capa.DataType  # mismo tipo de datos que la banda original
        )

        # Copiar georreferenciación y proyección
        mem_ds.SetGeoTransform(inDataSource.GetGeoTransform())
        mem_ds.SetProjection(inDataSource.GetProjection())

        # Escribir datos en la banda
        mem_band = mem_ds.GetRasterBand(1)
        mem_band.WriteArray(band_array)
        mem_band.SetNoDataValue(capa.GetNoDataValue())
            
        self.datasource = mem_ds
        return mem_ds

    def exportar(self, EPSG_Salida = None, outputFormat = 'GTiff', WLD = False, PAM = False):
        """
        Exporta el ráster a un formato especificado (GTiff, JPEG, etc).

        Parámetros
        ----------
        EPSG_Salida : int o str, opcional
            Código EPSG del sistema de referencia de salida.
        outputFormat : str, opcional
            Formato de salida (por ejemplo, 'GTiff', 'JPEG').
        WLD : bool, opcional
            Si es True, genera archivo worldfile.
        PAM : bool, opcional
            Si es True, fuerza la creación de archivo PAM (.aux.xml) si es posible.

        Retorna
        -------
        bytes
            Archivo exportado como blob o como json (OGC API - Coverage).
        """
        gdal.UseExceptions()

        if self.datasource is None:
            raise Exception("Primero debes llamar a leer()")
        
        dato = self.datasource

        if outputFormat == 'json' or outputFormat == 'application/json':
            # Convertir a JSON (OGC API - Coverage)
            def gen_covjson_gdal():
                """
                Genera una representación CoverageJSON usando GDAL.
                Obtiene los metadatos a partir de self.datasource.obtener_atributos().
                """
                metadata = self.propiedades_cobertura()
                dataset = self.datasource  # el GDAL dataset interno

                minx, miny, maxx, maxy = metadata['bbox']

                cj = {
                    'type': 'Coverage',
                    'domain': {
                        'type': 'Domain',
                        'domainType': 'Grid',
                        'axes': {
                            'x': {
                                'start': minx,
                                'stop': maxx,
                                'num': metadata['width']
                            },
                            'y': {
                                'start': maxy,  # invertido porque coordenadas Y
                                'stop': miny,
                                'num': metadata['height']
                            }
                        },
                        'referencing': [{
                            'coordinates': ['x', 'y'],
                            'system': {
                                'type': metadata['crs_type'],
                                'id': metadata['bbox_crs']
                            }
                        }]
                    },
                    'parameters': {},
                    'ranges': {}
                }

                # Bandas
                bands_select = metadata.get('bands') or range(1, dataset.RasterCount + 1)

                for bs in bands_select:
                    band = dataset.GetRasterBand(bs)
                    band_name = f'band_{bs}'
                    description = band.GetDescription() or f'Band {bs}'
                    unit = band.GetUnitType() or ''

                    parameter = {
                        'type': 'Parameter',
                        'description': {'en': description},
                        'unit': {'symbol': unit},
                        'observedProperty': {
                            'id': band_name,
                            'label': {'en': description}
                        }
                    }

                    cj['parameters'][band_name] = parameter

                    arr = band.ReadAsArray()

                    cj['ranges'][band_name] = {
                        'type': 'NdArray',
                        'dataType': gdal.GetDataTypeName(band.DataType).lower(),
                        'axisNames': ['y', 'x'],
                        'shape': [band.YSize, band.XSize],
                        'values': arr.flatten().tolist()
                    }

                return cj

            json = gen_covjson_gdal()
            return json
        
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


        if PAM:
            gdal.SetConfigOption('GDAL_PAM_ENABLED', 'YES')
        else:
            gdal.SetConfigOption('GDAL_PAM_ENABLED', 'NO')

        dato = gdal.Warp(outputPath, dato, options=warp_options, format=outputFormat)

        if PAM:
            dato.SetMetadata({
                'proyecto': 'pygdal_PG_datasource',
                'autor': 'A²',
            })
            dato.FlushCache()

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

    def propiedades_cobertura(self):
        """
        Obtiene las propiedades de la cobertura ráster.

        Retorna
        -------
        dict
            Diccionario con las propiedades de la cobertura.
        """
        if self.datasource is None:
            raise Exception("Primero debes llamar a leer()")

        gt = self.datasource.GetGeoTransform()
        width = self.datasource.RasterXSize
        height = self.datasource.RasterYSize

        # Cálculo de bounding box (esquina superior izquierda y pixel size)
        minx = gt[0]
        maxy = gt[3]
        maxx = minx + (width * gt[1])
        miny = maxy + (height * gt[5])  # gt[5] es negativo para north-up

        # Resoluciones
        resx = gt[1]
        resy = abs(gt[5])

        # Número de bandas
        num_bands = self.datasource.RasterCount

        # Proyección
        proj_wkt = self.datasource.GetProjection()
        srs = osr.SpatialReference()
        srs.ImportFromWkt(proj_wkt) if proj_wkt else None

        properties = {
            'bbox': [minx, miny, maxx, maxy],
            'bbox_crs': 'http://www.opengis.net/def/crs/OGC/1.3/CRS84',
            'crs_type': 'GeographicCRS',
            'bbox_units': 'deg',
            'x_axis_label': 'Long',
            'y_axis_label': 'Lat',
            'width': width,
            'height': height,
            'resx': resx,
            'resy': resy,
            'num_bands': num_bands,
            'tags': self.datasource.GetMetadata()
        }

        # Si tiene proyección definida
        if proj_wkt:
            if srs.IsProjected():
                epsg_code = srs.GetAttrValue("AUTHORITY", 1)
                if epsg_code:
                    properties['bbox_crs'] = f'http://www.opengis.net/def/crs/EPSG/0/{epsg_code}'
                properties['x_axis_label'] = 'x'
                properties['y_axis_label'] = 'y'
                properties['bbox_units'] = srs.GetLinearUnitsName() or 'm'
                properties['crs_type'] = 'ProjectedCRS'
            else:
                # CRS geográfico
                epsg_code = srs.GetAttrValue("AUTHORITY", 1)
                if epsg_code:
                    properties['bbox_crs'] = f'http://www.opengis.net/def/crs/EPSG/0/{epsg_code}'
                properties['bbox_units'] = srs.GetAngularUnitsName() or 'deg'

        properties['axes'] = [
            properties['x_axis_label'], properties['y_axis_label']
        ]

        return properties

    def obtener_atributos(self, banda=None):
        """
        Devuelve los atributos (metadatos) de una o todas las bandas.
        
        :param banda: (int) Número de la banda (1-indexada).
                    Si es None, se devuelven todas las bandas.
        :return: dict con atributos de la banda o de todas las bandas.
        """
        if self.datasource is None:
            raise Exception("Primero debes llamar a leer()")

        atributos = {}

        # Número total de bandas
        num_bandas = self.datasource.RasterCount

        # Función para procesar una banda
        def _procesar_banda(idx):
            band = self.datasource.GetRasterBand(idx)
            if band is None:
                return None

            # Tipo de datos
            dtype = gdal.GetDataTypeName(band.DataType).lower()
            if dtype.startswith('float'):
                dtype2 = 'float'
            elif dtype.startswith('int') or dtype.startswith('uint'):
                dtype2 = 'integer'
            else:
                dtype2 = 'string'

            return {
                'title': band.GetDescription() or f'Band {idx}',
                'type': dtype2,
                'unit': band.GetUnitType() or None,
                'metadata': band.GetMetadata(),
                'statistics': band.GetStatistics(True, True)  # [min, max, mean, std]
            }

        # Si se pide una banda específica
        if banda is not None:
            if banda < 1 or banda > num_bandas:
                raise ValueError(f"La banda {banda} no existe. Hay {num_bandas} bandas.")
            return _procesar_banda(banda)

        # Si no se indica banda, devolver todas
        for i in range(1, num_bandas + 1):
            atributos[str(i)] = _procesar_banda(i)

        return atributos

    def gdalinfo_2_json(self):
        """
        Devuelve un diccionario con información similar a `gdalinfo` para el dataset dado.
        """
        if self.datasource is None:
            raise ValueError("El dataset no está abierto.")

        info = {}

        # Tamaño de la imagen
        info['size'] = [self.datasource.RasterXSize, self.datasource.RasterYSize]
        
        # Driver
        driver = self.datasource.GetDriver()
        info['driver'] = {
            'short_name': driver.ShortName,
            'long_name': driver.LongName
        }

        # Proyección
        projection = self.datasource.GetProjection()
        info['projection'] = projection if projection else "Sin proyección"

        # GeoTransform
        geotransform = self.datasource.GetGeoTransform()
        if geotransform:
            info['geotransform'] = {
                'origin': [geotransform[0], geotransform[3]],
                'pixel_size': [geotransform[1], geotransform[5]]
            }

        # Metadata general
        info['metadata'] = self.datasource.GetMetadata()

        # Bandas
        bands_info = []
        for i in range(1, self.datasource.RasterCount + 1):
            band = self.datasource.GetRasterBand(i)
            band_info = {
                'band': i,
                'data_type': gdal.GetDataTypeName(band.DataType),
                'size': [band.XSize, band.YSize],
                'color_interp': gdal.GetColorInterpretationName(band.GetColorInterpretation()),
                'statistics': None,
                'nodata_value': band.GetNoDataValue()
            }

            # Estadísticas
            try:
                stats = band.GetStatistics(True, True)
                band_info['statistics'] = {
                    'min': stats[0],
                    'max': stats[1],
                    'mean': stats[2],
                    'stddev': stats[3]
                }
            except:
                band_info['statistics'] = "No disponibles"

            # Metadata de la banda
            band_info['metadata'] = band.GetMetadata()

            bands_info.append(band_info)

        info['bands'] = bands_info

        return info

    def MRE_datos(self, banda=None, MRE=[-180, -90, 180, 90], EPSG_MRE=4326):
        """
        Recorta self.datasource físicamente al bbox MRE, actualizando self.datasource.
        Si banda es None, recorta todas las bandas; si no, sólo la banda indicada.

        :param banda: int, número de banda (1-based) o None para todas
        :param MRE: [minx, miny, maxx, maxy] bbox en EPSG_MRE
        :param EPSG_MRE: EPSG del bbox de entrada
        :return: lista de arrays numpy de las bandas recortadas
        """

        if self.datasource is None:
            raise Exception("Dataset no cargado")

        # Obtener CRS del dataset
        ds_srs_wkt = self.datasource.GetProjection()
        ds_srs = osr.SpatialReference()
        ds_srs.ImportFromWkt(ds_srs_wkt)

        # CRS del bbox
        src_srs = osr.SpatialReference()
        if "EPSG" in str(EPSG_MRE):
            EPSG_MRE = EPSG_MRE.split(":")[1]
        src_srs.ImportFromEPSG(int(EPSG_MRE))

        # Detectar si los CRS usan orden YX
        def _coords_invertidas(srs):
            return srs.EPSGTreatsAsLatLong() or srs.EPSGTreatsAsNorthingEasting()

        src_invert = _coords_invertidas(src_srs)
        dst_invert = _coords_invertidas(ds_srs)

        # Si los órdenes no coinciden, invertimos el bbox de entrada
        minx, miny, maxx, maxy = MRE
        if src_invert != dst_invert:
            minx, miny, maxx, maxy = miny, minx, maxy, maxx

        # Transformar bbox
        if not src_srs.IsSame(ds_srs):
            transform = osr.CoordinateTransformation(src_srs, ds_srs)
            (minx_t, miny_t, _) = transform.TransformPoint(minx, miny)
            (maxx_t, maxy_t, _) = transform.TransformPoint(maxx, maxy)
            MRE_ds = [min(minx_t, maxx_t), min(miny_t, maxy_t), max(minx_t, maxx_t), max(miny_t, maxy_t)]
        else:
            MRE_ds = [minx, miny, maxx, maxy]


        # Geotransform original
        gt = self.datasource.GetGeoTransform()
        inv_gt = gdal.InvGeoTransform(gt)
        if inv_gt is None:
            raise Exception("No se pudo invertir la geotransformación")

        # Calcular offsets en píxeles y tamaño
        px_min = int(gdal.ApplyGeoTransform(inv_gt, MRE_ds[0], MRE_ds[3])[0])
        py_min = int(gdal.ApplyGeoTransform(inv_gt, MRE_ds[0], MRE_ds[3])[1])
        px_max = int(gdal.ApplyGeoTransform(inv_gt, MRE_ds[2], MRE_ds[1])[0])
        py_max = int(gdal.ApplyGeoTransform(inv_gt, MRE_ds[2], MRE_ds[1])[1])

        # Ajustar límites a tamaño del dataset
        px_min = max(0, min(self.datasource.RasterXSize, px_min))
        px_max = max(0, min(self.datasource.RasterXSize, px_max))
        py_min = max(0, min(self.datasource.RasterYSize, py_min))
        py_max = max(0, min(self.datasource.RasterYSize, py_max))

        xsize = px_max - px_min
        ysize = py_max - py_min

        if xsize <= 0 or ysize <= 0:
            raise Exception("BBox recortado no válido")

        # Crear dataset en memoria para recorte
        driver = gdal.GetDriverByName('MEM')

        bands_to_process = range(1, self.datasource.RasterCount + 1) if banda is None else [banda]
        nbands = len(bands_to_process)

        # Usar tipo de dato de la primera banda para el dataset nuevo (puedes mejorarlo para multi banda con distinto tipo)
        band_type = self.datasource.GetRasterBand(bands_to_process[0]).DataType

        out_ds = driver.Create('', xsize, ysize, nbands, band_type)
        out_ds.SetProjection(ds_srs_wkt)

        # Calcular nuevo geotransform para el recorte
        new_gt = list(gt)
        # Esquina superior izquierda en coordenadas reales según el offset px_min, py_min
        new_gt[0], new_gt[3] = gdal.ApplyGeoTransform(gt, px_min, py_min)
        out_ds.SetGeoTransform(new_gt)

        # Copiar datos banda a banda
        for i, b in enumerate(bands_to_process, start=1):
            in_band = self.datasource.GetRasterBand(b)
            out_band = out_ds.GetRasterBand(i)

            data = in_band.ReadAsArray(px_min, py_min, xsize, ysize)
            out_band.WriteArray(data)

            # Copiar NoData si existe
            nodata = in_band.GetNoDataValue()
            if nodata is not None:
                out_band.SetNoDataValue(float(nodata))

            out_band.FlushCache()

        # Finalmente, asignar out_ds a self.datasource
        self.datasource = out_ds

        # Opcional: devolver arrays recortados para uso inmediato
        arrays = [self.datasource.GetRasterBand(i).ReadAsArray() for i in range(1, nbands + 1)]

        return arrays

    def extraer_bandas(self, bandas):
        """
        Crea un nuevo dataset en memoria con las bandas seleccionadas,
        reemplaza self.datasource y devuelve un array con los objetos banda.

        :param bandas: lista de enteros (1-based) indicando las bandas deseadas
        :return: lista de objetos gdal.Band del nuevo dataset
        """
        if self.datasource is None:
            raise Exception("Dataset no cargado")

        if not bandas:
            raise Exception("Debe especificar al menos una banda")

        max_band = self.datasource.RasterCount
        bandas = [int(b) for b in bandas]
        for b in bandas:
            if b < 1 or b > max_band:
                raise Exception(f"Banda {b} fuera de rango (1-{max_band})")

        # Obtener tamaño, proyección y geotransformación del dataset original
        xsize = self.datasource.RasterXSize
        ysize = self.datasource.RasterYSize
        proj = self.datasource.GetProjection()
        geotransform = self.datasource.GetGeoTransform()

        # Usar el tipo de la primera banda seleccionada (puedes adaptarlo si son distintos)
        band_type = self.datasource.GetRasterBand(bandas[0]).DataType

        # Crear nuevo dataset en memoria
        driver = gdal.GetDriverByName('MEM')
        out_ds = driver.Create('', xsize, ysize, len(bandas), band_type)
        out_ds.SetProjection(proj)
        out_ds.SetGeoTransform(geotransform)

        # Copiar las bandas seleccionadas
        for i, b in enumerate(bandas, start=1):
            in_band = self.datasource.GetRasterBand(b)
            out_band = out_ds.GetRasterBand(i)

            # Copiar datos
            data = in_band.ReadAsArray()
            out_band.WriteArray(data)

            # Copiar nodata si existe
            nodata = in_band.GetNoDataValue()
            if nodata is not None:
                out_band.SetNoDataValue(float(nodata))

            out_band.FlushCache()

        # Reemplazar el dataset original por el nuevo
        self.datasource = out_ds

        # Devolver lista de objetos banda del nuevo dataset
        return [self.datasource.GetRasterBand(i) for i in range(1, len(bandas) + 1)]

       