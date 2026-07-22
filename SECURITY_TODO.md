# Pendiente de seguridad — Purga de credenciales del historial de git

> **Estado: PENDIENTE.** Las credenciales ya NO están en el working tree (se
> eliminaron con la carpeta `test/`), pero **siguen presentes en el historial de
> git** y son recuperables desde cualquier clon del repositorio (que es público).

## Qué pasó

En commits antiguos, bajo `test/files/`, se versionaron ficheros con credenciales
reales:

- `test/files/params_tuyaSmartLife.json` — password Tuya, contraseñas WiFi,
  `AccessID`, `AccessSecret`, `access_token`, `refresh_token`.
- `test/files/devices_sonoff.sqlite`, `test/files/devices_tuyaSmartLife.json` —
  posibles `devicekey` / tokens de dispositivos.

## Acciones (en orden)

- [ ] **1. Rotar TODAS las credenciales comprometidas** (lo más urgente; hazlo aunque
      no purgues el historial todavía):
  - [ ] Cambiar la contraseña de la cuenta Tuya.
  - [ ] Regenerar `AccessID` / `AccessSecret` en la Tuya IoT Platform.
  - [ ] Invalidar/rotar `access_token` y `refresh_token` de Tuya.
  - [ ] Cambiar las contraseñas WiFi de los routers afectados.
  - [ ] Revisar credenciales eWeLink/Sonoff si aplica.

- [ ] **2. Sacar copia de seguridad** de los ficheros de credenciales que aún
      necesites (fuera del repo).

- [ ] **3. Purgar el historial** con [`git filter-repo`](https://github.com/newren/git-filter-repo):

  ```bash
  # Instalar (una vez):  pip install git-filter-repo
  # Desde la raíz del repo (idealmente sobre un clon fresco):
  git filter-repo --path test/files --invert-paths
  # Si quieres eliminar toda la carpeta test/ del historial:
  # git filter-repo --path test --invert-paths
  ```

- [ ] **4. Reconfigurar el remoto y force-push** (filter-repo elimina el remoto):

  ```bash
  git remote add origin https://github.com/IngenieroGeomatico/pygdal_PG_datasource.git
  git push --force --all
  git push --force --tags
  ```

- [ ] **5. Verificar** que los secretos ya no aparecen en el historial:

  ```bash
  git log --all --oneline -- "test/files/*"      # no debe devolver nada
  git grep -i "AccessSecret" $(git rev-list --all)  # no debe encontrar coincidencias
  ```

- [ ] **6. Avisar a colaboradores**: tras reescribir el historial, cualquier clon
      existente queda desincronizado y debe volver a clonarse.

## Prevención (ya aplicada)

- `.gitignore` endurecido: ignora `params_*.json`, `devices_*.json`, `*.sqlite`,
  `PGconex.json`, `tests/files/`, `test/files/`.
- Los tests de integración leen credenciales de **variables de entorno**, no de
  ficheros versionados (ver sección *Tests* del README).
