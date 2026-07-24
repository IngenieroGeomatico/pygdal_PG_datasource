# Utilidades compartidas de GDAL/OGR.
#
# Centraliza:
#   - La comprobación diferida de disponibilidad de GDAL (``asegurar_gdal``).
#   - El diagnóstico de instalación y listado de drivers (``probar_gdal_ogr``).
#   - La normalización de códigos EPSG (``normalizar_epsg``).
#
# El import de ``osgeo`` se difiere: importar este módulo NO aborta el proceso
# cuando GDAL no está instalado (p. ej. al ejecutar tests de lógica pura). El
# error solo se lanza cuando se intenta usar GDAL de verdad.

import sys
import logging

logger = logging.getLogger(__name__)

try:
    from osgeo import ogr, osr, gdal  # noqa: F401  (osr reexportado por conveniencia)
    _GDAL_IMPORT_ERROR = None
except Exception as _exc:  # pragma: no cover - depende del entorno
    ogr = osr = gdal = None
    _GDAL_IMPORT_ERROR = _exc


def asegurar_gdal(componente="esta funcionalidad"):
    """Lanza un ImportError claro si GDAL/OGR (paquete ``osgeo``) no está disponible.

    Parámetros
    ----------
    componente : str
        Texto descriptivo del componente que requiere GDAL, usado para
        construir un mensaje de error contextual (p. ej. ``"FuenteDatosVector"``).
    """
    if _GDAL_IMPORT_ERROR is not None:
        raise ImportError(
            f"GDAL/OGR (paquete 'osgeo') no está disponible. "
            f"Instálalo para usar {componente}."
        ) from _GDAL_IMPORT_ERROR


def normalizar_epsg(epsg):
    """Normaliza un código EPSG a ``int``.

    Acepta ``int`` (se devuelve tal cual), o ``str`` en formatos como
    ``"EPSG:25830"``, ``"epsg:25830"`` o ``"25830"``. Ignora espacios.

    Devuelve
    --------
    int
        El código EPSG numérico.
    """
    if isinstance(epsg, str):
        epsg = epsg.replace(" ", "")
        if ":" in epsg:
            epsg = epsg.split(":")[1]
    return int(epsg)


def probar_gdal_ogr():
    """Comprueba la instalación de GDAL/OGR y muestra los drivers disponibles.

    Herramienta de diagnóstico interactiva: imprime a consola la versión de GDAL
    y la lista de drivers vectoriales y ráster.
    """
    asegurar_gdal("el diagnóstico de GDAL/OGR")
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
