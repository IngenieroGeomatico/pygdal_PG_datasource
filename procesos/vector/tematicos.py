from osgeo import ogr

def crear_atributo_area_OGR(layer, nombre_capa_salida, nombre_atributo="area_m2"):
    """
    Crea una nueva capa copiando todas las geometrías de la capa original y
    añade un campo con el área de cada geometría.

    :param layer: objeto ogr.Layer con geometrías de entrada
    :param nombre_capa_salida: nombre para la nueva capa
    :param nombre_atributo: nombre del campo que contendrá el área
    :return: nueva capa (ogr.Layer) en memoria
    """
    driver = ogr.GetDriverByName("Memory")
    ds_area = driver.CreateDataSource("area_ds")

    srs = layer.GetSpatialRef()
    geom_type = layer.GetGeomType()

    # Crear la nueva capa
    area_layer = ds_area.CreateLayer(nombre_capa_salida, srs=srs, geom_type=geom_type)

    # Copiar campos del layer original
    layer_defn = layer.GetLayerDefn()
    for i in range(layer_defn.GetFieldCount()):
        area_layer.CreateField(layer_defn.GetFieldDefn(i))

    # Añadir el nuevo campo para el área
    field_area = ogr.FieldDefn(nombre_atributo, ogr.OFTReal)
    field_area.SetWidth(32)
    field_area.SetPrecision(3)
    area_layer.CreateField(field_area)

    area_defn = area_layer.GetLayerDefn()

    # Iterar sobre las features de la capa original
    for feature in layer:
        geom = feature.GetGeometryRef()
        if geom:
            area = geom.GetArea()  # Área en unidades del SRS

            new_feature = ogr.Feature(area_defn)
            new_feature.SetGeometry(geom.Clone())  # Clonar geometría para la nueva capa

            # Copiar atributos originales
            for i in range(layer_defn.GetFieldCount()):
                new_feature.SetField(i, feature.GetField(i))

            # Asignar el área
            new_feature.SetField(nombre_atributo, area)

            area_layer.CreateFeature(new_feature)
            new_feature = None

    layer.ResetReading()
    return ds_area, area_layer