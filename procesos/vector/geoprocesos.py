from osgeo import ogr

def crear_capa_buffer_OGR(layer, distancia_buffer, nombre_capa_salida=None):
    """
    Crea una nueva capa con buffers de cada geometría de la capa original.

    :param layer: objeto ogr.Layer con geometrías de entrada
    :param distancia_buffer: distancia para generar el buffer (en las mismas unidades del SRS)
    :param nombre_capa_salida: nombre para la capa buffer (por defecto usa el mismo nombre que layer)
    :return: nueva capa (ogr.Layer) en memoria con las geometrías bufferizadas
    """
    driver = ogr.GetDriverByName("Memory")
    ds_buffer = driver.CreateDataSource("buffer_ds")

    srs = layer.GetSpatialRef()
    geom_type = ogr.wkbPolygon  # El buffer es siempre un polígono

    if nombre_capa_salida is None:
        nombre_capa_salida = layer.GetName()

    buffer_layer = ds_buffer.CreateLayer(nombre_capa_salida, srs=srs, geom_type=geom_type)

    # Copiar campos del layer original para que se mantengan en la capa buffer
    layer_defn = layer.GetLayerDefn()
    for i in range(layer_defn.GetFieldCount()):
        buffer_layer.CreateField(layer_defn.GetFieldDefn(i))

    buffer_defn = buffer_layer.GetLayerDefn()

    # Iterar sobre features y crear buffer
    for feature in layer:
        geom = feature.GetGeometryRef()
        if geom:
            geom_buffer = geom.Buffer(distancia_buffer)

            buffer_feature = ogr.Feature(buffer_defn)
            buffer_feature.SetGeometry(geom_buffer)

            # Copiar atributos de la feature original
            for i in range(layer_defn.GetFieldCount()):
                buffer_feature.SetField(i, feature.GetField(i))

            buffer_layer.CreateFeature(buffer_feature)
            buffer_feature = None

    layer.ResetReading()
    return ds_buffer, buffer_layer