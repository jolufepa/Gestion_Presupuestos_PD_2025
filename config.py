# config.py
import os
import sys

def get_application_path():
    """
    Obtiene la ruta del directorio donde se ejecuta la aplicación.
    Funciona para desarrollo (.py) y para producción (.exe).
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

# Configuración de rutas
app_path = get_application_path()
DB_PATH = os.path.join(app_path, 'data', 'clinica_dental.db')
KEY_PATH = os.path.join(app_path, 'data', 'app.key')
PDF_DIR = os.path.join(app_path, "data", "presupuestos_pdf")
DATA_DIR = os.path.join(app_path, 'data')
BACKUP_DIR = os.path.join(app_path, 'backups')

# Asegurar que los directorios existen
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

# Configuración de la clínica
CLINIC_CONFIG = {
    "name": "Clínica Dental P&D",
    "cif": "J-66472580", 
    "address": "Rambla Just Oliveras, 56 2º 2ª",
    "postal_code": "08901 L'Hospitalet de Llobregat (Barcelona)",
    "phone": "933377714",
    "email": "pddental22@gmail.com"
}

# Configuración de seguridad
SECRET_KEY = "0tONl5rIqubrEBL1po5h6Pha1r0cIb"

# Configuración de la aplicación
APP_VERSION = "1.0"
APP_NAME = "Clínica Dental - Gestión"