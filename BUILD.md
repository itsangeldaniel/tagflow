name: Build TagFlow

on:
  push:
    tags:
      - 'v*'

jobs:

  build-linux:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install PyQt6 send2trash pyinstaller
      - run: |
          pyinstaller --onefile --windowed --name TagFlow \
            --hidden-import PyQt6 \
            --hidden-import PyQt6.QtCore \
            --hidden-import PyQt6.QtGui \
            --hidden-import PyQt6.QtWidgets \
            --hidden-import send2trash \
            main.py
      - uses: actions/upload-artifact@v4
        with:
          name: TagFlow-Linux
          path: dist/TagFlow

  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install PyQt6 send2trash pyinstaller
      - name: Compilar
        run: |
          pyinstaller --onefile --windowed --name TagFlow `
            --hidden-import PyQt6 `
            --hidden-import PyQt6.QtCore `
            --hidden-import PyQt6.QtGui `
            --hidden-import PyQt6.QtWidgets `
            --hidden-import send2trash `
            main.py
      - name: Comprimir en zip
        run: Compress-Archive -Path dist\TagFlow.exe -DestinationPath dist\TagFlow-Windows.zip
      - uses: actions/upload-artifact@v4
        with:
          name: TagFlow-Windows
          path: dist/TagFlow-Windows.zip

  build-macos:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install PyQt6 send2trash pyinstaller
      - name: Compilar como app bundle (onedir)
        run: |
          pyinstaller --onedir --windowed --name TagFlow \
            --hidden-import PyQt6 \
            --hidden-import PyQt6.QtCore \
            --hidden-import PyQt6.QtGui \
            --hidden-import PyQt6.QtWidgets \
            --hidden-import send2trash \
            main.py
      - name: Comprimir en zip
        run: |
          cd dist
          zip -r TagFlow-macOS.zip TagFlow.app
      - uses: actions/upload-artifact@v4
        with:
          name: TagFlow-macOS
          path: dist/TagFlow-macOS.zip

  release:
    needs: [build-linux, build-windows, build-macos]
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: TagFlow-Linux
          path: artifacts/linux
      - uses: actions/download-artifact@v4
        with:
          name: TagFlow-Windows
          path: artifacts/windows
      - uses: actions/download-artifact@v4
        with:
          name: TagFlow-macOS
          path: artifacts/macos
      - run: |
          mv artifacts/linux/TagFlow artifacts/TagFlow-Linux
          mv artifacts/windows/TagFlow-Windows.zip artifacts/TagFlow-Windows.zip
          mv artifacts/macos/TagFlow-macOS.zip artifacts/TagFlow-macOS.zip
          chmod +x artifacts/TagFlow-Linux
      - uses: softprops/action-gh-release@v2
        with:
          files: |
            artifacts/TagFlow-Linux
            artifacts/TagFlow-Windows.zip
            artifacts/TagFlow-macOS.zip
          body: |
            ## TagFlow ${{ github.ref_name }}

            - **Linux** → `TagFlow-Linux` — dar permiso: `chmod +x TagFlow-Linux` y ejecutar
            - **Windows** → `TagFlow-Windows.zip` — descomprimir y ejecutar `TagFlow.exe`
            - **macOS** → `TagFlow-macOS.zip` — descomprimir, clic derecho en `TagFlow.app` → Abrir