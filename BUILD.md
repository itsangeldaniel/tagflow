# Compilar TagFlow como ejecutable

## Requisitos
```bash
pip install pyinstaller send2trash PyQt6 --break-system-packages
```

## Antes de compilar
1. Edita `updater.py` y pon tu usuario y repo de GitHub:
   ```python
   GITHUB_OWNER = "tu-usuario-github"
   GITHUB_REPO  = "tagflow"
   ```
2. Actualiza `version.txt` con la versión actual (ej: `1.0.0`)

## Compilar

### Linux
```bash
pyinstaller tagflow.spec
# Ejecutable en: dist/TagFlow
```

### Windows (desde Windows)
```bash
pyinstaller tagflow.spec
# Ejecutable en: dist/TagFlow.exe
```

### macOS (desde Mac)
```bash
pyinstaller tagflow.spec
# App en: dist/TagFlow.app
```

## Publicar una actualización
1. Incrementa la versión en `version.txt` (ej: `1.0.1`)
2. Compila el ejecutable para cada plataforma
3. Ve a GitHub → tu repo → Releases → "Create new release"
4. Tag: `v1.0.1`
5. Sube los archivos:
   - `TagFlow` (Linux)
   - `TagFlow.exe` (Windows)
   - `TagFlow.dmg` (macOS)
6. Publica el release

Los usuarios con TagFlow abierto verán el aviso de actualización
automáticamente en los próximos 30 segundos de uso.

## Notas
- El ejecutable pesa ~80-120 MB (PyQt6 es grande)
- El auto-update requiere conexión a internet solo para verificar
- Los datos del usuario (carpetas, colores, notas) nunca se tocan
