# utils.py - VERSIÓN SIMPLIFICADA
import sys
import os

# Esta función ahora está en config.py, pero la mantenemos por compatibilidad
def get_application_path():
    """
    Obtiene la ruta del directorio donde se ejecuta la aplicación.
    Funciona para desarrollo (.py) y para producción (.exe).
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

def resource_path(relative_path):
    """ Obtiene la ruta absoluta a un recurso, funciona para desarrollo y para PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)