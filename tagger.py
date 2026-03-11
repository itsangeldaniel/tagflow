import re
import os

# ──────────────────────────────────────────────────────────────
#  PARSER – Extrae etiquetas del nombre del archivo
#  Soporta subcarpetas: @carpeta@sub@subsub
# ──────────────────────────────────────────────────────────────

_TAG = r'[a-zA-Z0-9_\-áéíóúüñÁÉÍÓÚÜÑ]+'


def extraer_etiqueta(nombre_archivo: str) -> str | None:
    """
    Compatibilidad con código existente.
    Retorna solo la primera etiqueta o None.
    """
    ruta = extraer_ruta(nombre_archivo)
    return ruta[0] if ruta else None


def extraer_ruta(nombre_archivo: str) -> list[str] | None:
    """
    Extrae todas las etiquetas @A@B@C como lista ['A','B','C'].
    Representa la ruta de carpetas anidadas.

    Ejemplos:
        "doc@trabajo.pdf"              → ['trabajo']
        "doc@trabajo@proyectos.pdf"    → ['trabajo', 'proyectos']
        "foto@viaje@2024@verano.jpg"   → ['viaje', '2024', 'verano']
        "sin_etiqueta.txt"             → None
    """
    # Buscar bloque de @etiquetas consecutivas
    matches = re.findall(r'@(' + _TAG + r')', nombre_archivo)
    return matches if matches else None


def nombre_limpio(nombre_archivo: str) -> str:
    """
    Retorna el nombre del archivo sin las etiquetas @.
    "doc@trabajo@proyectos.pdf" → "doc.pdf"
    """
    # Quitar todo el bloque @etiqueta@etiqueta...
    nombre, ext = os.path.splitext(nombre_archivo)
    nombre_sin = re.sub(r'(@' + _TAG + r')+', '', nombre).strip()
    return (nombre_sin or "archivo") + ext