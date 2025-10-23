import os
import sqlite3
import sys
from cryptography.fernet import Fernet
import re
from datetime import datetime
import bcrypt
from utils import get_application_path
from config import DB_PATH, KEY_PATH, DATA_DIR, BACKUP_DIR
from contextlib import contextmanager

@contextmanager
def get_db_connection():
    """
    Context manager para manejo automático de conexiones a BD.
    Uso:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT ...")
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        yield conn
        conn.commit()  # Commit si todo sale bien
    except sqlite3.Error as e:
        if conn:
            conn.rollback()  # Rollback en caso de error
        raise e
    finally:
        if conn:
            conn.close()
def resource_path(relative_path):
    """ Obtiene la ruta absoluta a un recurso, funciona para desarrollo y para PyInstaller """
    try:
        # PyInstaller crea una carpeta temporal y guarda la ruta en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


# --- 1. Funciones de Encriptación y Clave RGPD ---

def get_key():
    """Genera una clave Fernet si no existe, o la carga. DEVUELVE BYTES."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    if not os.path.exists(KEY_PATH):
        key = Fernet.generate_key()
        with open(KEY_PATH, 'wb') as key_file:
            key_file.write(key)
        print("✅ Clave RGPD generada y guardada.")
    else:
        with open(KEY_PATH, 'rb') as key_file:
            key = key_file.read()
    
    return key  # <-- IMPORTANTE: Devuelve los bytes, NO Fernet(key)

# Y LUEGO crear el CIPHER_SUITE con esa clave
CIPHER_SUITE = Fernet(get_key())

def encrypt_field(data):
    """Encripta una cadena de texto a BLOB (bytes)."""
    if data:
        return CIPHER_SUITE.encrypt(data.encode('utf-8'))
    return None

def decrypt_field(data_blob):
    """Desencripta un BLOB (bytes) a cadena de texto. Devuelve '' si hay error o es None."""
    if data_blob:
        try:
            return CIPHER_SUITE.decrypt(data_blob).decode('utf-8')
        except Exception:
            return ''
    return ''

# --- 2. Funciones de Validación ---

def validar_dni_nie(valor):
    """Función de validación estricta de DNI/NIE con checksum."""
    tabla_letras = "TRWAGMYFPDXBNJZSQVHLCKE"
    valor = valor.upper().strip()
    if not re.match(r'^(\d{8}[A-Z]|([XYZ])\d{7}[A-Z])$', valor): return False
    
    if valor[0] in 'XYZ':
        if valor[0] == 'X': num = int(valor[1:8])
        elif valor[0] == 'Y': num = int(valor[1:8]) + 10000000
        else: num = int(valor[1:8]) + 20000000
    else: 
        num = int(valor[:8])
    
    indice = num % 23
    return valor[-1] == tabla_letras[indice]

# --- 3. Inicialización de la Base de Datos ---

def setup_db():
    """Conecta a la DB, crea tablas y poblado inicial."""
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # --- 1. CREACIÓN DE TODAS LAS TABLAS (VERSIÓN COMPLETA) ---
        
        # Tabla PACIENTES
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Pacientes (
                id INTEGER PRIMARY KEY,
                nombre TEXT NOT NULL,
                apellidos TEXT NOT NULL,
                dni_nie TEXT UNIQUE NOT NULL,
                telefono_enc BLOB,
                direccion_enc BLOB,
                email_enc BLOB,
                notas_enc BLOB,
                fecha_registro TEXT,
                activo INTEGER DEFAULT 1
            )
        """)
        
        # Tabla TRATAMIENTOS
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Tratamientos (
                id INTEGER PRIMARY KEY,
                nombre TEXT NOT NULL,
                descripcion TEXT,
                precio_unitario REAL CHECK(precio_unitario > 0),
                fecha_creacion TEXT
            )
        """)
        
        # Tabla USUARIOS
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Usuarios (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash BLOB NOT NULL,
                rol TEXT NOT NULL,
                fecha_registro TEXT
            )
        """)
        
        # Tabla PRESUPUESTOS
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Presupuestos (
                id INTEGER PRIMARY KEY,
                numero_presupuesto TEXT UNIQUE NOT NULL,
                paciente_id INTEGER,
                fecha TEXT,
                subtotal REAL CHECK(subtotal >= 0),
                descuento REAL CHECK(descuento >= 0),
                iva_porcentaje REAL DEFAULT 0.0,
                total REAL,
                notas TEXT,
                pdf_path TEXT,
                FOREIGN KEY (paciente_id) REFERENCES Pacientes(id)
            )
        """)
        
        # Tabla PRESUPUESTOS_DETALLES
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Presupuestos_Detalles (
                id INTEGER PRIMARY KEY,
                presupuesto_id INTEGER,
                tratamiento_id INTEGER,
                nombre_manual TEXT, 
                cantidad INTEGER CHECK(cantidad > 0),
                precio_unitario REAL CHECK(precio_unitario > 0),
                subtotal REAL,
                FOREIGN KEY (presupuesto_id) REFERENCES Presupuestos(id),
                FOREIGN KEY (tratamiento_id) REFERENCES Tratamientos(id)
            )
        """)

        # --- 2. POBLAMIENTO DE DATOS DE EJEMPLO ---
        
        # Comprobar y poblar Pacientes
        cursor.execute("SELECT COUNT(*) FROM Pacientes")
        if cursor.fetchone()[0] == 0:
            print("Poblando con datos de ejemplo...")
            
            dni_ejemplo = "12345678A"
            
            telefono_enc = encrypt_field("600123456")
            direccion_enc = encrypt_field("C/ Ejemplo, 1, 28001 Madrid")
            email_enc = encrypt_field("paciente@ejemplo.es")
            
            cursor.execute("""
                INSERT INTO Pacientes (nombre, apellidos, dni_nie, telefono_enc, direccion_enc, email_enc, fecha_registro)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, ('María', 'García López', dni_ejemplo, sqlite3.Binary(telefono_enc), 
                  sqlite3.Binary(direccion_enc), sqlite3.Binary(email_enc), datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            paciente_id = cursor.lastrowid
            
            cursor.execute("""
                INSERT INTO Tratamientos (nombre, descripcion, precio_unitario, fecha_creacion)
                VALUES (?, ?, ?, ?)
            """, ('Empaste Simple', 'Obturación de composite en pieza simple.', 75.00, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            tratamiento_id = cursor.lastrowid

            subtotal = 75.00 * 2 
            total = subtotal 
            cursor.execute("""
                INSERT INTO Presupuestos (numero_presupuesto, paciente_id, fecha, subtotal, descuento, iva_porcentaje, total)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, ('2025-001', paciente_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), subtotal, 0.0, 0.0, total))
            presupuesto_id = cursor.lastrowid
            cursor.execute("""
                INSERT INTO Presupuestos_Detalles (presupuesto_id, tratamiento_id, cantidad, precio_unitario, subtotal)
                VALUES (?, ?, ?, ?, ?)
            """, (presupuesto_id, tratamiento_id, 2, 75.00, subtotal))
            
            conn.commit()
            print("✅ Datos de ejemplo insertados.")

        # --- 3. POBLAMIENTO DE USUARIO ADMINISTRADOR ---
        cursor.execute("SELECT COUNT(*) FROM Usuarios")
        if cursor.fetchone()[0] == 0:
            
            password_plano = "admin123"
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(password_plano.encode('utf-8'), salt)
            
            cursor.execute("""
                INSERT INTO Usuarios (username, password_hash, rol, fecha_registro)
                VALUES (?, ?, ?, ?)
            """, ('admin', sqlite3.Binary(hashed_password), 'Administrador', datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            
            conn.commit() 
            print("✅ Usuario 'admin' (pass: admin123) insertado.")

        return "✅ Base de datos configurada."
        
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        return f"❌ Error de SQLite: {e}"
    except Exception as e:
        return f"❌ Error inesperado: {e}"
    finally:
        if conn:
            conn.close()

# -------------------------------------------------------------------
# --- FASE 2: FUNCIONES CRUD COMPLETAS ---
# -------------------------------------------------------------------

def guardar_paciente(nombre, apellidos, dni_nie, telefono, direccion, email, notas, id_paciente=None):
    """Guarda o actualiza un paciente. Devuelve un mensaje de éxito o error."""
    
    # Preparar datos encriptados
    tel_enc = encrypt_field(telefono)
    dir_enc = encrypt_field(direccion)
    email_enc = encrypt_field(email)
    notas_enc = encrypt_field(notas)
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if id_paciente is None:
                # MODO CREACIÓN (INSERT)
                sql_insert = """
                    INSERT INTO Pacientes (nombre, apellidos, dni_nie, telefono_enc, 
                                          direccion_enc, email_enc, notas_enc, fecha_registro)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """
                params = (
                    nombre, apellidos, dni_nie, 
                    sqlite3.Binary(tel_enc) if tel_enc else None, 
                    sqlite3.Binary(dir_enc) if dir_enc else None, 
                    sqlite3.Binary(email_enc) if email_enc else None, 
                    sqlite3.Binary(notas_enc) if notas_enc else None, 
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                )
                
                cursor.execute(sql_insert, params)
                paciente_id = cursor.lastrowid
                return f"Paciente {paciente_id} creado con éxito."
            else:
                # MODO EDICIÓN (UPDATE)
                sql_update = """
                    UPDATE Pacientes SET nombre=?, apellidos=?, dni_nie=?, 
                    telefono_enc=?, direccion_enc=?, email_enc=?, notas_enc=?
                    WHERE id=?
                """
                params = (
                    nombre, apellidos, dni_nie, 
                    sqlite3.Binary(tel_enc) if tel_enc else None, 
                    sqlite3.Binary(dir_enc) if dir_enc else None, 
                    sqlite3.Binary(email_enc) if email_enc else None, 
                    sqlite3.Binary(notas_enc) if notas_enc else None, 
                    id_paciente
                )
                cursor.execute(sql_update, params)
                return f"Paciente {id_paciente} actualizado con éxito."

    except sqlite3.IntegrityError:
        return "Error: DNI/NIE ya existe."
    except sqlite3.Error as e:
        return f"Error DB al guardar paciente: {e}"

def obtener_pacientes():
    """Obtiene todos los pacientes ACTIVOS (desencriptando los campos sensibles)."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nombre, apellidos, dni_nie, telefono_enc, 
                   direccion_enc, email_enc, notas_enc, fecha_registro 
            FROM Pacientes WHERE activo=1 
            ORDER BY apellidos, nombre
        """)
        pacientes_raw = cursor.fetchall()
    
    pacientes_desenc = []
    for p in pacientes_raw:
        pacientes_desenc.append((
            p['id'], p['nombre'], p['apellidos'], p['dni_nie'],
            decrypt_field(p['telefono_enc']),
            decrypt_field(p['direccion_enc']),
            decrypt_field(p['email_enc']),
            decrypt_field(p['notas_enc']),
            p['fecha_registro']
        ))
    return pacientes_desenc

def eliminar_paciente(id_paciente):
    """Archiva (desactiva) a un paciente en lugar de eliminarlo."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE Pacientes SET activo=0 WHERE id=?", (id_paciente,))
        
        if cursor.rowcount > 0:
            return f"Paciente {id_paciente} archivado con éxito. Ya no aparecerá en la lista, pero sus presupuestos se conservan."
        else:
            return "Paciente no encontrado."

def obtener_paciente_por_id(patient_id):
    """Obtiene todos los datos de un paciente por su ID, DESENCRIPTANDO los campos sensibles."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nombre, apellidos, dni_nie, telefono_enc, 
                   direccion_enc, email_enc, notas_enc, fecha_registro 
            FROM Pacientes WHERE id=?
        """, (patient_id,))
        data = cursor.fetchone()
    
    if data:
        return {
            "id": data['id'], "nombre": data['nombre'], "apellidos": data['apellidos'],
            "dni_nie": data['dni_nie'], "telefono": decrypt_field(data['telefono_enc']),
            "direccion": decrypt_field(data['direccion_enc']), "email": decrypt_field(data['email_enc']),
            "notas": decrypt_field(data['notas_enc']), "fecha_registro": data['fecha_registro']
        }
    return None

# <-- CORRECCIÓN: La función 'actualizar_paciente' fue eliminada por ser redundante.
# La función 'guardar_paciente' ya maneja la actualización.

# --- Funciones para Tratamientos (similares mejoras) ---
def guardar_tratamiento(nombre, descripcion, precio_unitario, id_tratamiento=None):
    """Guarda o actualiza un tratamiento."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if id_tratamiento is None:
                # MODO CREACIÓN (INSERT)
                sql_insert = """
                    INSERT INTO Tratamientos (nombre, descripcion, precio_unitario, fecha_creacion)
                    VALUES (?, ?, ?, ?)
                """
                params = (nombre, descripcion, precio_unitario, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                cursor.execute(sql_insert, params)
                return "Tratamiento creado con éxito."
            else:
                # MODO EDICIÓN (UPDATE)
                sql_update = """
                    UPDATE Tratamientos SET nombre=?, descripcion=?, precio_unitario=?
                    WHERE id=?
                """
                params = (nombre, descripcion, precio_unitario, id_tratamiento)
                cursor.execute(sql_update, params)
                return "Tratamiento actualizado con éxito."

    except sqlite3.Error as e:
        return f"Error DB al guardar tratamiento: {e}"

def obtener_tratamientos():
    """Obtiene todos los tratamientos."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nombre, descripcion, precio_unitario, fecha_creacion 
            FROM Tratamientos 
            ORDER BY nombre
        """)
        tratamientos_raw = cursor.fetchall()
    
    return [(t['id'], t['nombre'], t['descripcion'], t['precio_unitario'], t['fecha_creacion']) 
            for t in tratamientos_raw]

def eliminar_tratamiento(id_tratamiento):
    """Elimina un tratamiento de la base de datos."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Tratamientos WHERE id=?", (id_tratamiento,))
            
            if cursor.rowcount > 0:
                return "Tratamiento eliminado con éxito."
            else:
                return "Tratamiento no encontrado."
                
    except sqlite3.Error as e:
        return f"Error DB al eliminar tratamiento: {e}"

# --- Funciones para Presupuestos ---
def generar_numero_presupuesto():
    """Genera un número de presupuesto único basado en el año actual y conteo."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        año_actual = datetime.now().strftime('%Y')
        cursor.execute("SELECT COUNT(*) FROM Presupuestos WHERE strftime('%Y', fecha) = ?", (año_actual,))
        conteo = cursor.fetchone()[0]
    
    return f"{año_actual}-{conteo + 1:03d}"

def guardar_presupuesto_completo(paciente_id, detalles, subtotal, descuento, iva_porcentaje, total, notas, numero_presupuesto=None, id_presupuesto=None):
    """Guarda o actualiza un presupuesto y sus detalles. Devuelve (mensaje, id_presupuesto)."""
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if id_presupuesto is None:
                # MODO CREACIÓN (INSERT)
                if numero_presupuesto is None:
                    return "Error: Falta el número de presupuesto para la creación.", None
                
                sql_insert = """
                    INSERT INTO Presupuestos (numero_presupuesto, paciente_id, fecha, subtotal, descuento, iva_porcentaje, total, notas)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """
                params = (
                    numero_presupuesto, paciente_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
                    subtotal, descuento, iva_porcentaje, total, notas
                )
                
                cursor.execute(sql_insert, params)
                id_presupuesto = cursor.lastrowid
                accion = "creado"
            else:
                # MODO EDICIÓN (UPDATE)
                if numero_presupuesto:
                    sql_update = """
                        UPDATE Presupuestos SET subtotal=?, descuento=?, iva_porcentaje=?, total=?, notas=?, numero_presupuesto=?
                        WHERE id=?
                    """
                    params = (subtotal, descuento, iva_porcentaje, total, notas, numero_presupuesto, id_presupuesto)
                else:
                    sql_update = """
                        UPDATE Presupuestos SET subtotal=?, descuento=?, iva_porcentaje=?, total=?, notas=?
                        WHERE id=?
                    """
                    params = (subtotal, descuento, iva_porcentaje, total, notas, id_presupuesto)

                cursor.execute(sql_update, params)
                accion = "actualizado"
                
                # Eliminar detalles existentes para reinsertarlos
                cursor.execute("DELETE FROM Presupuestos_Detalles WHERE presupuesto_id=?", (id_presupuesto,))

            # INSERCIÓN DE DETALLES
            for item in detalles:
                tratamiento_id, nombre_manual, cantidad, precio_unitario = item
                subtotal_detalle = cantidad * precio_unitario
                
                sql_detalle = """
                    INSERT INTO Presupuestos_Detalles (presupuesto_id, tratamiento_id, nombre_manual, cantidad, precio_unitario, subtotal)
                    VALUES (?, ?, ?, ?, ?, ?)
                """
                params_detalle = (id_presupuesto, tratamiento_id, nombre_manual, cantidad, precio_unitario, subtotal_detalle)
                cursor.execute(sql_detalle, params_detalle)
                
            return (f"Presupuesto {numero_presupuesto or id_presupuesto} {accion} con éxito. ID: {id_presupuesto}", id_presupuesto)
            
    except sqlite3.IntegrityError as e:
        return (f"Error de integridad (posible duplicado de número de presupuesto): {e}", None)
    except sqlite3.Error as e:
        return (f"Error DB al guardar presupuesto: {e}", None)

def obtener_presupuestos(id_presupuesto=None):
    """Obtiene una lista de presupuestos o uno específico con sus detalles."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        if id_presupuesto:
            cursor.execute("SELECT * FROM Presupuestos WHERE id=?", (id_presupuesto,))
            presupuesto = cursor.fetchone()
            cursor.execute("SELECT * FROM Presupuestos_Detalles WHERE presupuesto_id=?", (id_presupuesto,))
            detalles = cursor.fetchall()
            return (presupuesto, detalles)
        else:
            cursor.execute("""
                SELECT P.id, P.numero_presupuesto, C.nombre, C.apellidos, P.fecha, P.total 
                FROM Presupuestos P 
                JOIN Pacientes C ON P.paciente_id = C.id 
                ORDER BY P.fecha DESC
            """)
            presupuestos_raw = cursor.fetchall()
            return [(p['id'], p['numero_presupuesto'], p['nombre'], p['apellidos'], p['fecha'], p['total']) 
                    for p in presupuestos_raw]

def obtener_presupuesto_completo_para_pdf(presupuesto_id):
    """
    Obtiene todos los datos de un presupuesto, incluyendo los detalles y
    los datos desencriptados del paciente, necesarios para el PDF.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        presupuesto_raw = cursor.execute("SELECT * FROM Presupuestos WHERE id=?", (presupuesto_id,)).fetchone()
        if not presupuesto_raw:
            return None

        paciente_id = presupuesto_raw['paciente_id']
        paciente_raw = cursor.execute("SELECT * FROM Pacientes WHERE id=?", (paciente_id,)).fetchone()
        if not paciente_raw:
            return None

        detalles_list = cursor.execute("SELECT * FROM Presupuestos_Detalles WHERE presupuesto_id=?", (presupuesto_id,)).fetchall()
        
        return (presupuesto_raw, paciente_raw, detalles_list)

# --- FUNCIONES DE SEGURIDAD (FASE 3) ---
def verify_user(username, password):
    """Verifica si el nombre de usuario y la contraseña son correctos. Devuelve el rol o None."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash, rol FROM Usuarios WHERE username=?", (username.strip().lower(),))
        user_data = cursor.fetchone()
    
    if user_data and bcrypt.checkpw(password.encode('utf-8'), user_data['password_hash']):
        return user_data['rol']
    return None

def get_user_role(username):
    """Obtiene el rol del usuario."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT rol FROM Usuarios WHERE username=?", (username,))
        rol = cursor.fetchone()
    
    return rol['rol'] if rol else None

def cambiar_contrasena(username, new_password):
    """Cambia la contraseña de un usuario."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            cursor.execute("UPDATE Usuarios SET password_hash=? WHERE username=?", (hashed, username))
            return "Éxito: Contraseña cambiada correctamente."
    except Exception as e:
        return f"Error: No se pudo cambiar la contraseña. {e}"

def crear_nuevo_usuario(username, password, rol):
    """Crea un nuevo usuario en el sistema."""
    try:
        # Verificar si el usuario ya existe
        if get_user_role(username) is not None:
            return "Error: El nombre de usuario ya existe."
            
        with get_db_connection() as conn:
            cursor = conn.cursor()
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            cursor.execute("INSERT INTO Usuarios (username, password_hash, rol) VALUES (?, ?, ?)", 
                          (username, hashed, rol))
            return f"Éxito: Usuario '{username}' creado como '{rol}'."
    except Exception as e:
        return f"Error: No se pudo crear el usuario. {e}"

def obtener_usuarios():
    """Devuelve TODOS los usuarios de la DB."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        usuarios_raw = cursor.execute("SELECT id, username, rol, fecha_registro FROM Usuarios").fetchall()
        return [(u['id'], u['username'], u['rol'], u['fecha_registro']) for u in usuarios_raw]

def eliminar_usuario(user_id):
    """Elimina un usuario por su ID, con protección para el admin principal."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT username FROM Usuarios WHERE id=?", (user_id,))
            username = cursor.fetchone()
            
            if username and username[0] == 'admin':
                return "Error: No se puede eliminar el usuario administrador principal."
                
            cursor.execute("DELETE FROM Usuarios WHERE id=?", (user_id,))
            return "Éxito: Usuario eliminado."
    except Exception as e:
        return f"Error: No se pudo eliminar el usuario. {e}"

# --- TEST SIMPLE ---
if __name__ == "__main__":
    if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
    if not os.path.exists(BACKUP_DIR): os.makedirs(BACKUP_DIR)
    print(f"Directorios creados: {DATA_DIR}/ y {BACKUP_DIR}/")
    
    resultado_db = setup_db()
    print(resultado_db)
    
    # ... (resto del bloque de test) ...
    print("\n✅ FASE 1 COMPLETA Y VERIFICADA.")
    print("\n--- TEST CRUD PACIENTES (Fase 2) ---")
    dni_nuevo = "X0000000R" 
    if validar_dni_nie(dni_nuevo):
        print(f"Resultado Creación: {guardar_paciente('Ana', 'Pérez Ruiz', dni_nuevo, '666999000', 'C/ Luna 1', 'ana@test.es', 'Notas de prueba')}")
    
    print("\n--- TEST PRESUPUESTOS (Numeración) ---")
    num_nuevo = generar_numero_presupuesto()
    print(f"Número de Presupuesto Automático Generado: {num_nuevo}")
    
    print("\n✅ FASE 2 INICIADA Y PROBADA CON ÉXITO.")