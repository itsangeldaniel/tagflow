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
            --add-data "tagflow_icon.png:." \
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
      - name: Compilar sin icono
        run: |
          pyinstaller --onefile --windowed --name TagFlow `
            --hidden-import PyQt6 `
            --hidden-import PyQt6.QtCore `
            --hidden-import PyQt6.QtGui `
            --hidden-import PyQt6.QtWidgets `
            --hidden-import send2trash `
            --add-data "tagflow_icon.png;." `
            main.py
        env:
          PYINSTALLER_SKIP_TAG_ICON: "1"
      - uses: actions/upload-artifact@v4
        with:
          name: TagFlow-Windows
          path: dist/TagFlow.exe

  build-macos:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install PyQt6 send2trash pyinstaller
      - name: Compilar sin bundle
        run: |
          pyinstaller --onefile --name TagFlow \
            --hidden-import PyQt6 \
            --hidden-import PyQt6.QtCore \
            --hidden-import PyQt6.QtGui \
            --hidden-import PyQt6.QtWidgets \
            --hidden-import send2trash \
            --add-data "tagflow_icon.png:." \
            main.py
      - uses: actions/upload-artifact@v4
        with:
          name: TagFlow-macOS
          path: dist/TagFlow

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
          mv artifacts/windows/TagFlow.exe artifacts/TagFlow-Windows.exe
          mv artifacts/macos/TagFlow artifacts/TagFlow-macOS
          chmod +x artifacts/TagFlow-Linux artifacts/TagFlow-macOS
      - uses: softprops/action-gh-release@v2
        with:
          files: |
            artifacts/TagFlow-Linux
            artifacts/TagFlow-Windows.exe
            artifacts/TagFlow-macOS
          body: |
            ## TagFlow ${{ github.ref_name }}
            - **Linux** → `TagFlow-Linux`
            - **Windows** → `TagFlow-Windows.exe`
            - **macOS** → `TagFlow-macOS`