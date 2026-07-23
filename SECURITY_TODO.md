# Seguridad — Historial purgado

> **Estado: COMPLETADO.** El historial de git ha sido purgado de los archivos con
> credenciales mediante `git filter-repo --path test/files --invert-paths` y
> forzado al remoto.

## Qué pasó

En commits antiguos, bajo `test/files/`, se versionaron ficheros con credenciales
reales:

- `test/files/params_tuyaSmartLife.json` — password Tuya, contraseñas WiFi,
  `AccessID`, `AccessSecret`, `access_token`, `refresh_token`.
- `test/files/devices_sonoff.sqlite`, `test/files/devices_tuyaSmartLife.json` —
  posibles `devicekey` / tokens de dispositivos.

## Acciones ejecutadas

- [x] **1. Sacar copia de seguridad** de los ficheros de credenciales (fuera del repo).
- [x] **2. Purgar el historial** con `git filter-repo --path test/files --invert-paths`.
- [x] **3. Hacer force push** al remoto (`git push --force --all`).
- [x] **4. Verificar** que los secretos ya no aparecen en el historial.
- [ ] **5. Rotar TODAS las credenciales comprometidas** (tarea pendiente en los servicios externos):
  - [ ] Cambiar la contraseña de la cuenta Tuya.
  - [ ] Regenerar `AccessID` / `AccessSecret` en la Tuya IoT Platform.
  - [ ] Invalidar/rotar `access_token` y `refresh_token` de Tuya.
  - [ ] Cambiar las contraseñas WiFi de los routers afectados.
  - [ ] Revisar credenciales eWeLink/Sonoff si aplica.
- [ ] **6. Avisar a colaboradores**: cualquier clon existente está desincronizado y debe volver a clonarse.

## Prevención (ya aplicada)

- `.gitignore` endurecido: ignora `params_*.json`, `devices_*.json`, `*.sqlite`,
  `PGconex.json`, `tests/files/`, `test/files/`.
- Los tests de integración leen credenciales de **variables de entorno**, no de
  ficheros versionados.
