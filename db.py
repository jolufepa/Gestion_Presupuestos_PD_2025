import os
import sqlite3
from cryptography.fernet import Fernet
import re
from datetime import datetime
import bcrypt

# --- CONFIGURACIÓN GLOBAL ---
DB_PATH = 'data/clinica_dental.db'
KEY_PATH = 'data/app.key'
DATA_DIR = 'data'
BACKUP_DIR = 'backups'

# --- 1. Funciones de Encriptación y Clave RGPD ---

def get_key():
    """Genera una clave Fernet si no existe, o la carga."""
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
    
    return Fernet(key)

CIPHER_SUITE = get_key()

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
        # <-- MEJORA: Usar Row para acceso por nombre, aunque aquí no se explota mucho
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
                fecha_registro TEXT
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
        
        # Tabla USUARIOS (FASE 3)
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

        # --- 2. POBLAMIENTO DE DATOS DE EJEMPLO (Pacientes/Tratamientos) ---
        
        # Comprobar y poblar Pacientes
        cursor.execute("SELECT COUNT(*) FROM Pacientes")
        if cursor.fetchone()[0] == 0:
            print("Poblando con datos de ejemplo...")
            
            dni_ejemplo = "12345678A"
            
            telefono_enc = encrypt_field("600123456")
            direccion_enc = encrypt_field("C/ Ejemplo, 1, 28001 Madrid")
            email_enc = encrypt_field("paciente@ejemplo.es")
            
            # 1. Inserción Paciente
            cursor.execute("""
                INSERT INTO Pacientes (nombre, apellidos, dni_nie, telefono_enc, direccion_enc, email_enc, fecha_registro)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, ('María', 'García López', dni_ejemplo, sqlite3.Binary(telefono_enc), 
                  sqlite3.Binary(direccion_enc), sqlite3.Binary(email_enc), datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            paciente_id = cursor.lastrowid
            
            # 2. Inserción Tratamiento
            cursor.execute("""
                INSERT INTO Tratamientos (nombre, descripcion, precio_unitario, fecha_creacion)
                VALUES (?, ?, ?, ?)
            """, ('Empaste Simple', 'Obturación de composite en pieza simple.', 75.00, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            tratamiento_id = cursor.lastrowid

            # 3. Inserción Presupuesto y Detalle
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
            
            # Commit de los datos de ejemplo (Pacientes/Tratamientos)
            conn.commit()
            print("✅ Datos de ejemplo insertados.")


        # --- 3. POBLAMIENTO DE USUARIO ADMINISTRADOR (Separado y con su propia comprobación) ---
        cursor.execute("SELECT COUNT(*) FROM Usuarios")
        if cursor.fetchone()[0] == 0:
            
            password_plano = "admin123"
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(password_plano.encode('utf-8'), salt)
            
            cursor.execute("""
                INSERT INTO Usuarios (username, password_hash, rol, fecha_registro)
                VALUES (?, ?, ?, ?)
            """, ('admin', sqlite3.Binary(hashed_password), 'Administrador', datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            
            conn.commit() # Commit SOLO para el usuario admin
            print("✅ Usuario 'admin' (pass: admin123) insertado.")


        return "✅ Base de datos configurada."
        
    except sqlite3.Error as e:
        # Se asegura de que la conexión exista antes de hacer rollback
        if conn:
            conn.rollback()
        return f"❌ Error de SQLite: {e}"
    except Exception as e:
        return f"❌ Error inesperado: {e}"
    finally:
        # Cierra la conexión UNA SOLA VEZ
        if conn:
            conn.close()

# -------------------------------------------------------------------
# --- FASE 2: FUNCIONES CRUD COMPLETAS ---
# -------------------------------------------------------------------

def guardar_paciente(nombre, apellidos, dni_nie, telefono, direccion, email, notas, id_paciente=None):
    """Guarda o actualiza un paciente. Devuelve un mensaje de éxito o error."""
    # <-- MEJORA: Usar Row para consistencia
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    tel_enc = encrypt_field(telefono)
    dir_enc = encrypt_field(direccion)
    email_enc = encrypt_field(email)
    notas_enc = encrypt_field(notas)
    
    try:
        if id_paciente is None:
            # --- MODO CREACIÓN (INSERT) ---
            sql_insert = """
                INSERT INTO Pacientes (nombre, apellidos, dni_nie, telefono_enc, direccion_enc, email_enc, notas_enc, fecha_registro)
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
            
            # <-- INICIO DE LA DEPURACIÓN
            print("--- DEPURACIÓN: Guardar Paciente (INSERT) ---")
            print("SQL a ejecutar:")
            print(sql_insert)
            print("Parámetros:")
            print(params)
            print("-------------------------------------------")
            # <-- FIN DE LA DEPURACIÓN

            cursor.execute(sql_insert, params)
            paciente_id = cursor.lastrowid
            conn.commit()
            return f"Paciente {paciente_id} creado con éxito."
        else:
            # --- MODO EDICIÓN (UPDATE) ---
            sql_update = """
                UPDATE Pacientes SET nombre=?, apellidos=?, dni_nie=?, telefono_enc=?, direccion_enc=?, email_enc=?, notas_enc=?
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
            conn.commit()
            return f"Paciente {id_paciente} actualizado con éxito."

    except sqlite3.IntegrityError:
        return "Error: DNI/NIE ya existe."
    except sqlite3.Error as e:
        # <-- INICIO DE LA DEPURACIÓN
        print("--- DEPURACIÓN: Error de SQLite ---")
        print(f"Error detectado: {e}")
        print("-------------------------------------")
        # <-- FIN DE LA DEPURACIÓN
        return f"Error DB al guardar paciente: {e}"
    finally:
        conn.close()

def obtener_pacientes():
    """Obtiene todos los pacientes (desencriptando los campos sensibles)."""
    # <-- MEJORA: Usar Row para acceso por nombre y mayor robustez
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, apellidos, dni_nie, telefono_enc, direccion_enc, email_enc, notas_enc, fecha_registro FROM Pacientes ORDER BY apellidos, nombre")
    pacientes_raw = cursor.fetchall()
    conn.close()
    
    pacientes_desenc = []
    for p in pacientes_raw:
        # Acceso por nombre es más seguro y legible
        paciente_tuple = (
            p['id'], p['nombre'], p['apellidos'], p['dni_nie'],
            decrypt_field(p['telefono_enc']),
            decrypt_field(p['direccion_enc']),
            decrypt_field(p['email_enc']),
            decrypt_field(p['notas_enc']),
            p['fecha_registro']
        )
        pacientes_desenc.append(paciente_tuple)
        
    return pacientes_desenc

def eliminar_paciente(id_paciente):
    """Elimina un paciente por ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Pacientes WHERE id=?", (id_paciente,))
        conn.commit()
        if cursor.rowcount > 0:
            return f"Paciente {id_paciente} eliminado con éxito."
        else:
            return "Paciente no encontrado."
    except sqlite3.Error as e:
        return f"Error DB al eliminar paciente: {e}"
    finally:
        conn.close()

def obtener_paciente_por_id(patient_id):
    """Obtiene todos los datos de un paciente por su ID, DESENCRIPTANDO los campos sensibles."""
    # <-- MEJORA: Usar Row para acceso por nombre
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        cursor.execute("""SELECT id, nombre, apellidos, dni_nie, telefono_enc, direccion_enc, email_enc, notas_enc, fecha_registro FROM Pacientes WHERE id=?""", (patient_id,))
        data = cursor.fetchone()
        
        if data:
            # El objeto 'data' (Row) ya tiene acceso por nombre, lo convertimos a diccionario para la GUI
            return {
                "id": data['id'], "nombre": data['nombre'], "apellidos": data['apellidos'],
                "dni_nie": data['dni_nie'], "telefono": decrypt_field(data['telefono_enc']),
                "direccion": decrypt_field(data['direccion_enc']), "email": decrypt_field(data['email_enc']),
                "notas": decrypt_field(data['notas_enc']), "fecha_registro": data['fecha_registro']
            }
        return None
    except Exception as e:
        print(f"Error al obtener y desencriptar paciente ID {patient_id}: {e}")
        return None
    finally:
        conn.close()

# <-- CORRECCIÓN: La función 'actualizar_paciente' fue eliminada por ser redundante.
# La función 'guardar_paciente' ya maneja la actualización.

# --- Funciones para Tratamientos (similares mejoras) ---
def guardar_tratamiento(nombre, descripcion, precio_unitario, id_tratamiento=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        if id_tratamiento is None:
            cursor.execute("""INSERT INTO Tratamientos (...) VALUES (?, ?, ?, ?)""", (nombre, descripcion, precio_unitario, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            conn.commit()
            return "Tratamiento creado con éxito."
        else:
            cursor.execute("""UPDATE Tratamientos SET nombre=?, descripcion=?, precio_unitario=? WHERE id=?""", (nombre, descripcion, precio_unitario, id_tratamiento))
            conn.commit()
            return "Tratamiento actualizado con éxito."
    except sqlite3.Error as e:
        return f"Error DB al guardar tratamiento: {e}"
    finally:
        conn.close()

def obtener_tratamientos():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row # <-- MEJORA
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, descripcion, precio_unitario, fecha_creacion FROM Tratamientos ORDER BY nombre")
    tratamientos_raw = cursor.fetchall()
    conn.close()
    # Convertir a tuplas para compatibilidad con la GUI
    return [(t['id'], t['nombre'], t['descripcion'], t['precio_unitario'], t['fecha_creacion']) for t in tratamientos_raw]

def eliminar_tratamiento(id_tratamiento):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Tratamientos WHERE id=?", (id_tratamiento,))
        conn.commit()
        if cursor.rowcount > 0: return "Tratamiento eliminado con éxito."
        else: return "Tratamiento no encontrado."
    except sqlite3.Error as e:
        return f"Error DB al eliminar tratamiento: {e}"
    finally:
        conn.close()

# --- Funciones para Presupuestos ---
def generar_numero_presupuesto():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    año_actual = datetime.now().strftime('%Y')
    cursor.execute("""SELECT COUNT(*) FROM Presupuestos WHERE strftime('%Y', fecha) = ?""", (año_actual,))
    conteo = cursor.fetchone()[0]
    conn.close()
    return f"{año_actual}-{conteo + 1:03d}"

def guardar_presupuesto_completo(paciente_id, detalles, subtotal, descuento, iva_porcentaje, total, notas, numero_presupuesto=None, id_presupuesto=None):
    """Guarda o actualiza un presupuesto y sus detalles. Devuelve (mensaje, id_presupuesto)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        if id_presupuesto is None:
            # --- MODO CREACIÓN (INSERT) ---
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
            
            # <-- INICIO DE LA DEPURACIÓN (INSERT) ---
            print("--- DEPURACIÓN: Guardar Presupuesto (INSERT) ---")
            print("SQL a ejecutar:")
            print(sql_insert)
            print("Parámetros:")
            print(params)
            print("----------------------------------------------")
            # <-- FIN DE LA DEPURACIÓN ---

            cursor.execute(sql_insert, params)
            id_presupuesto = cursor.lastrowid
            accion = "creado"
        else:
            # --- MODO EDICIÓN (UPDATE) ---
            # <-- CORRECCIÓN: Consulta parametrizada para evitar inyección SQL
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

            # <-- INICIO DE LA DEPURACIÓN (UPDATE) ---
            print("--- DEPURACIÓN: Guardar Presupuesto (UPDATE) ---")
            print("SQL a ejecutar:")
            print(sql_update)
            print("Parámetros:")
            print(params)
            print("----------------------------------------------")
            # <-- FIN DE LA DEPURACIÓN ---

            cursor.execute(sql_update, params)
            accion = "actualizado"
            
            cursor.execute("DELETE FROM Presupuestos_Detalles WHERE presupuesto_id=?", (id_presupuesto,))

        # --- INSERCIÓN DE DETALLES ---
        for item in detalles:
            tratamiento_id, nombre_manual, cantidad, precio_unitario = item
            subtotal_detalle = cantidad * precio_unitario
            
            sql_detalle = """
                INSERT INTO Presupuestos_Detalles (presupuesto_id, tratamiento_id, nombre_manual, cantidad, precio_unitario, subtotal)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            params_detalle = (id_presupuesto, tratamiento_id, nombre_manual, cantidad, precio_unitario, subtotal_detalle)

            # <-- INICIO DE LA DEPURACIÓN (DETALLES) ---
            print("--- DEPURACIÓN: Guardar Detalle del Presupuesto ---")
            print("SQL a ejecutar:")
            print(sql_detalle)
            print("Parámetros:")
            print(params_detalle)
            print("----------------------------------------------------")
            # <-- FIN DE LA DEPURACIÓN ---

            cursor.execute(sql_detalle, params_detalle)
            
        conn.commit()
        return (f"Presupuesto {numero_presupuesto or id_presupuesto} {accion} con éxito. ID: {id_presupuesto}", id_presupuesto)
        
    except sqlite3.IntegrityError as e:
        conn.rollback()
        print("--- DEPURACIÓN: Error de Integridad ---")
        print(f"Error detectado: {e}")
        print("-----------------------------------------")
        return (f"Error de integridad (posible duplicado de número de presupuesto): {e}", None)
    except sqlite3.Error as e:
        conn.rollback()
        # <-- INICIO DE LA DEPURACIÓN (ERROR GENERAL) ---
        print("--- DEPURACIÓN: Error General de SQLite ---")
        print(f"Error detectado: {e}")
        print("--------------------------------------------")
        # <-- FIN DE LA DEPURACIÓN ---
        return (f"Error DB al guardar presupuesto: {e}", None)
    finally:
        conn.close()

def obtener_presupuestos(id_presupuesto=None):
    """Obtiene una lista de presupuestos o uno específico con sus detalles."""
    # <-- MEJORA: Usar Row
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if id_presupuesto:
        cursor.execute("SELECT * FROM Presupuestos WHERE id=?", (id_presupuesto,))
        presupuesto = cursor.fetchone()
        cursor.execute("SELECT * FROM Presupuestos_Detalles WHERE presupuesto_id=?", (id_presupuesto,))
        detalles = cursor.fetchall()
        conn.close()
        # Devolver los objetos Row directamente para que el PDF los use por nombre
        return (presupuesto, detalles)
    else:
        cursor.execute("""SELECT P.id, P.numero_presupuesto, C.nombre, C.apellidos, P.fecha, P.total FROM Presupuestos P JOIN Pacientes C ON P.paciente_id = C.id ORDER BY P.fecha DESC""")
        presupuestos_raw = cursor.fetchall()
        conn.close()
        # Convertir a tuplas para compatibilidad con la GUI
        return [(p['id'], p['numero_presupuesto'], p['nombre'], p['apellidos'], p['fecha'], p['total']) for p in presupuestos_raw]

def obtener_presupuesto_completo_para_pdf(presupuesto_id):
    """
    Obtiene todos los datos de un presupuesto, incluyendo los detalles y
    los datos desencriptados del paciente, necesarios para el PDF.
    Devuelve (presupuesto_data, paciente_data, detalles_list) como objetos Row.
    """
    # <-- MEJORA: Usar Row para que el PDF acceda por nombre
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    presupuesto_raw = cursor.execute("SELECT * FROM Presupuestos WHERE id=?", (presupuesto_id,)).fetchone()
    if not presupuesto_raw: return None

    paciente_id = presupuesto_raw['paciente_id']
    paciente_raw = cursor.execute("SELECT * FROM Pacientes WHERE id=?", (paciente_id,)).fetchone()
    if not paciente_raw: return None

    # No es necesario desencriptar aquí, el PDF lo hará. Pasamos los Row objects.
    detalles_list = cursor.execute("SELECT * FROM Presupuestos_Detalles WHERE presupuesto_id=?", (presupuesto_id,)).fetchall()
    
    conn.close()
    return (presupuesto_raw, paciente_raw, detalles_list)

# --- FUNCIONES DE SEGURIDAD (FASE 3) ---
def verify_user(username, password):
    """Verifica si el nombre de usuario y la contraseña son correctos. Devuelve el rol o None."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row # <-- MEJORA
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash, rol FROM Usuarios WHERE username=?", (username.strip().lower(),))
    user_data = cursor.fetchone()
    conn.close()
    
    if user_data and bcrypt.checkpw(password.encode('utf-8'), user_data['password_hash']):
        return user_data['rol'] # Acceso por nombre
    return None

def get_user_role(username):
    """Obtiene el rol del usuario."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row # <-- MEJORA
    cursor = conn.cursor()
    cursor.execute("SELECT rol FROM Usuarios WHERE username=?", (username,))
    rol = cursor.fetchone()
    conn.close()
    return rol['rol'] if rol else None

def cambiar_contrasena(username, new_password):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        cursor.execute("UPDATE Usuarios SET password_hash=? WHERE username=?", (hashed, username))
        conn.commit()
        return "Éxito: Contraseña cambiada correctamente."
    except Exception as e:
        return f"Error: No se pudo cambiar la contraseña. {e}"
    finally:
        conn.close()

def crear_nuevo_usuario(username, password, rol):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        if get_user_role(username) is not None: return "Error: El nombre de usuario ya existe."
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        cursor.execute("INSERT INTO Usuarios (username, password_hash, rol) VALUES (?, ?, ?)", (username, hashed, rol))
        conn.commit()
        return f"Éxito: Usuario '{username}' creado como '{rol}'."
    except Exception as e:
        return f"Error: No se pudo crear el usuario. {e}"
    finally:
        conn.close()

def obtener_usuarios():
    """Devuelve TODOS los usuarios de la DB."""
    # <-- MEJORA: Usar Row
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    usuarios = []
    try:
        usuarios_raw = cursor.execute("SELECT id, username, rol, fecha_registro FROM Usuarios").fetchall()
        # Convertir a tuplas para la GUI
        usuarios = [(u['id'], u['username'], u['rol'], u['fecha_registro']) for u in usuarios_raw]
        return usuarios
    except Exception as e:
        print(f"Error CRÍTICO al obtener usuarios: {e}")
        return []
    finally:
        conn.close()

def eliminar_usuario(user_id):
    """Elimina un usuario por su ID, con protección para el admin principal."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT username FROM Usuarios WHERE id=?", (user_id,))
        username = cursor.fetchone()
        if username and username[0] == 'admin':
            return "Error: No se puede eliminar el usuario administrador principal."
        cursor.execute("DELETE FROM Usuarios WHERE id=?", (user_id,))
        conn.commit()
        return "Éxito: Usuario eliminado."
    except Exception as e:
        return f"Error: No se pudo eliminar el usuario. {e}"
    finally:
        conn.close()

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