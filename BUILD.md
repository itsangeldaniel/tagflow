name: Build TagFlow

on:
  push:
    tags:
      - 'v*'

jobs:

  # ── Linux ──────────────────────────────────────────────────
  build-linux:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Instalar dependencias
        run: pip install PyQt6 send2trash pyinstaller Pillow

      - name: Compilar
        run: |
          pyinstaller --onefile --windowed --name TagFlow \
            --hidden-import PyQt6 \
            --hidden-import PyQt6.QtCore \
            --hidden-import PyQt6.QtGui \
            --hidden-import PyQt6.QtWidgets \
            --hidden-import send2trash \
            --add-data "tagflow_icon.png:." \
            main.py

      - name: Subir ejecutable
        uses: actions/upload-artifact@v4
        with:
          name: TagFlow-Linux
          path: dist/TagFlow

  # ── Windows ────────────────────────────────────────────────
  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Instalar dependencias
        run: pip install PyQt6 send2trash pyinstaller Pillow

      - name: Convertir icono a .ico
        run: |
          python -c "
          from PIL import Image
          img = Image.open('tagflow_icon.png').convert('RGBA')
          img.save('tagflow_icon.ico', format='ICO', sizes=[(256,256),(128,128),(64,64),(32,32),(16,16)])
          print('icono convertido OK')
          "

      - name: Compilar
        run: |
          pyinstaller --onefile --windowed --name TagFlow `
            --icon=tagflow_icon.ico `
            --hidden-import PyQt6 `
            --hidden-import PyQt6.QtCore `
            --hidden-import PyQt6.QtGui `
            --hidden-import PyQt6.QtWidgets `
            --hidden-import send2trash `
            --add-data "tagflow_icon.png;." `
            main.py

      - name: Subir ejecutable
        uses: actions/upload-artifact@v4
        with:
          name: TagFlow-Windows
          path: dist/TagFlow.exe

  # ── macOS ──────────────────────────────────────────────────
  build-macos:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Instalar dependencias
        run: pip install PyQt6 send2trash pyinstaller Pillow

      - name: Convertir icono a .icns
        run: |
          mkdir -p tagflow_icon.iconset
          python3 -c "
          from PIL import Image
          img = Image.open('tagflow_icon.png').convert('RGBA')
          sizes = [16,32,64,128,256,512]
          for s in sizes:
              img.resize((s,s), Image.LANCZOS).save(f'tagflow_icon.iconset/icon_{s}x{s}.png')
              img.resize((s*2,s*2), Image.LANCZOS).save(f'tagflow_icon.iconset/icon_{s}x{s}@2x.png')
          "
          iconutil -c icns tagflow_icon.iconset -o tagflow_icon.icns

      - name: Compilar
        run: |
          pyinstaller --onefile --windowed --name TagFlow \
            --icon=tagflow_icon.icns \
            --hidden-import PyQt6 \
            --hidden-import PyQt6.QtCore \
            --hidden-import PyQt6.QtGui \
            --hidden-import PyQt6.QtWidgets \
            --hidden-import send2trash \
            --add-data "tagflow_icon.png:." \
            main.py

      - name: Subir ejecutable
        uses: actions/upload-artifact@v4
        with:
          name: TagFlow-macOS
          path: dist/TagFlow

  # ── Crear Release con los 3 ejecutables ───────────────────
  release:
    needs: [build-linux, build-windows, build-macos]
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - name: Descargar Linux
        uses: actions/download-artifact@v4
        with:
          name: TagFlow-Linux
          path: artifacts/linux

      - name: Descargar Windows
        uses: actions/download-artifact@v4
        with:
          name: TagFlow-Windows
          path: artifacts/windows

      - name: Descargar macOS
        uses: actions/download-artifact@v4
        with:
          name: TagFlow-macOS
          path: artifacts/macos

      - name: Renombrar ejecutables
        run: |
          mv artifacts/linux/TagFlow artifacts/TagFlow-Linux
          mv artifacts/windows/TagFlow.exe artifacts/TagFlow-Windows.exe
          mv artifacts/macos/TagFlow artifacts/TagFlow-macOS
          chmod +x artifacts/TagFlow-Linux artifacts/TagFlow-macOS

      - name: Crear Release
        uses: softprops/action-gh-release@v2
        with:
          files: |
            artifacts/TagFlow-Linux
            artifacts/TagFlow-Windows.exe
            artifacts/TagFlow-macOS
          body: |
            ## TagFlow ${{ github.ref_name }}

            ### Descargar
            - **Linux** → `TagFlow-Linux`
            - **Windows** → `TagFlow-Windows.exe`
            - **macOS** → `TagFlow-macOS`

            ### Instalación
            - **Linux/macOS**: `chmod +x TagFlow-Linux && ./TagFlow-Linux`
            - **Windows**: doble clic en el `.exe`