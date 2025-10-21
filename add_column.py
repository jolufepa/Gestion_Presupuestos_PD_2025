import sqlite3
from db import DB_PATH

try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("ALTER TABLE Pacientes ADD COLUMN activo INTEGER DEFAULT 1")
    conn.commit()
    conn.close()
    print("¡Éxito! La columna 'activo' ha sido añadida a la tabla Pacientes.")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("La columna 'activo' ya existía. No se ha hecho ningún cambio.")
    else:
        print(f"Ocurrió un error: {e}")
except Exception as e:
    print(f"Ha ocurrido un error inesperado: {e}")
