# TODO

## 🐛 Bugs

- [ ] `sonoff_conex.py:895,901,988` — `raise Exception(f,"...")` con coma en vez de f-string
- [ ] `Raster_conex.py:471` — expresión condicional que no hace nada (`... if proj_wkt else None`)

## ♻️ Duplicación

- [ ] Extraer `_asegurar_gdal()` y `probar_gdal_ogr()` a un módulo compartido
- [ ] Extraer normalización de EPSG (`if "EPSG" in str(x): x = x.split(":")[1]`) a helper
- [ ] Extraer bucle de copia de campos OGR (~8 apariciones) a función reutilizable
- [ ] Extraer bucle de copia de features OGR (~6 apariciones) a función reutilizable

## 🏗️ Estructura

- [ ] Dividir `Vector_conex.exportar` (~230 líneas) en métodos más pequeños
- [ ] Dividir `Vector_conex.leer` separando detección de tipo (WKT/OGR), prefijos VSI y copia a memoria
- [ ] Reemplazar `print()` por el módulo `logging`
- [ ] Añadir `pyproject.toml` para instalación con `pip install .`

## 🚀 Nuevas funcionalidades

- [ ] Añadir a `infoTuyaSmartLife` métodos de exportación geográfica (GeoJSON/OGR/SQLite) similares a los de Sonoff

## 🏷️ Nombres

- [ ] Unificar idioma (español → inglés): `leer`→`read`, `exportar`→`export`, `obtener_capas`→`get_layers`, etc.
- [ ] Unificar convención de nombres (snake_case en todo el código)
