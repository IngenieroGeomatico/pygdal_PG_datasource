# TODO

## 🐛 Bugs

- [x] `sonoff_conex.py` — `raise Exception(f,"...")` con coma en vez de f-string (3 casos corregidos)
- [x] `Raster_conex.py` — expresión ternaria `... if proj_wkt else None` reescrita como `if` normal

## ♻️ Duplicación

- [x] Extraer `_asegurar_gdal()` y `probar_gdal_ogr()` a módulo compartido (`conex/gdal_utils.py`)
- [x] Extraer normalización de EPSG a helper `normalizar_epsg()` (en `conex/gdal_utils.py`)
- [ ] Extraer bucle de copia de campos OGR (~9 apariciones) a función reutilizable
- [ ] Extraer bucle de copia de features OGR (~8 apariciones) a función reutilizable

  > ⚠️ **Diferido a propósito.** Es la parte más compleja y con estado (procesa
  > geometrías/atributos OGR). Sin cobertura de tests para las rutas GDAL
  > (`osgeo` no instalado + faltan fixtures en `tests/files/`), refactorizar aquí
  > arriesga corrupción silenciosa de datos. Retomar cuando los tests GDAL corran.

## 🏗️ Estructura

- [ ] Dividir `Vector_conex.exportar` (~230 líneas) en métodos más pequeños

  > ⚠️ **Diferido.** Método grande y crítico. Requiere red de seguridad de tests
  > (GDAL) antes de trocearlo con seguridad.

- [ ] Dividir `Vector_conex.leer` separando detección de tipo (WKT/OGR), prefijos VSI y copia a memoria *(nice-to-have, ~124 líneas; baja prioridad)*
- [x] Reemplazar `print()` por el módulo `logging` (se conservan a propósito los `print` de `probar_gdal_ogr()`, que es diagnóstico interactivo)
- [x] Añadir `pyproject.toml` para instalación con `pip install .`

## 🚀 Nuevas funcionalidades

- [x] Añadir a `infoTuyaSmartLife` métodos de exportación geográfica (GeoJSON/OGR/SQLite) similares a los de Sonoff

## 🏷️ Nombres

- [ ] ~~Unificar idioma (español → inglés)~~ *(descartado: es un breaking change de
  la API pública sin valor funcional; rompería README, ejemplos y los proyectos
  que consumen esta librería)*
- [ ] Unificar convención de nombres a snake_case *(cosmético, baja prioridad)*

## 🧪 Precondición para retomar lo diferido

- [ ] Instalar GDAL (`osgeo`) en el entorno de test y generar fixtures sin
  credenciales en `tests/files/`, de modo que los tests GDAL dejen de saltarse.
  Es el desbloqueo necesario para los refactores OGR marcados como diferidos.
