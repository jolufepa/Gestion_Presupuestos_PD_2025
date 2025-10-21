import os
import sqlite3
from cryptography.fernet import Fernet
import re
from datetime import datetime
import bcrypt # <-- ¡NUEVA IMPORTACIÓN!

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
    
    # Si la clave no existe, la genera y la guarda
    if not os.path.exists(KEY_PATH):
        key = Fernet.generate_key()
        with open(KEY_PATH, 'wb') as key_file:
            key_file.write(key)
        print("✅ Clave RGPD generada y guardada.")
    else:
        # Si existe, la carga
        with open(KEY_PATH, 'rb') as key_file:
            key = key_file.read()
    
    return Fernet(key)

# Instancia de Fernet para encriptar/desencriptar
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

# --- 3. Inicialización de la Base de Datos (Corregida) ---

def setup_db():
    """Conecta a la DB, crea tablas y poblado inicial."""
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # --- 1. CREACIÓN DE TODAS LAS TABLAS ---
        
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
# --- FASE 2: FUNCIONES CRUD COMPLETAS (AÑADIDAS PARA LA EJECUCIÓN) ---
# -------------------------------------------------------------------

def guardar_paciente(nombre, apellidos, dni_nie, telefono, direccion, email, notas, id_paciente=None):
    """Guarda o actualiza un paciente. Devuelve el ID o un mensaje de error."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. ENCRIPTACIÓN de campos sensibles (usa su función auxiliar)
    # Nota: dni_nie NO se encripta, se guarda como texto plano.
    tel_enc = encrypt_field(telefono)
    dir_enc = encrypt_field(direccion)
    email_enc = encrypt_field(email)
    notas_enc = encrypt_field(notas)
    
    try:
        if id_paciente is None:
            # --- MODO CREACIÓN (INSERT) ---
            cursor.execute("""
                INSERT INTO Pacientes (nombre, apellidos, dni_nie, telefono_enc, direccion_enc, email_enc, notas_enc, fecha_registro)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (nombre, apellidos, dni_nie, sqlite3.Binary(tel_enc) if tel_enc else None, 
                  sqlite3.Binary(dir_enc) if dir_enc else None, sqlite3.Binary(email_enc) if email_enc else None, 
                  sqlite3.Binary(notas_enc) if notas_enc else None, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            paciente_id = cursor.lastrowid
            conn.commit()
            return f"Paciente {paciente_id} creado con éxito."
        else:
            # --- MODO EDICIÓN (UPDATE) ---
            cursor.execute("""
                UPDATE Pacientes SET nombre=?, apellidos=?, dni_nie=?, telefono_enc=?, direccion_enc=?, email_enc=?, notas_enc=?
                WHERE id=?
            """, (nombre, apellidos, dni_nie, sqlite3.Binary(tel_enc) if tel_enc else None, 
                  sqlite3.Binary(dir_enc) if dir_enc else None, sqlite3.Binary(email_enc) if email_enc else None, 
                  sqlite3.Binary(notas_enc) if notas_enc else None, id_paciente))
            
            conn.commit()
            # Esta línea confirma que el UPDATE se ejecutó (aunque podría no haber cambiado nada)
            return f"Paciente {id_paciente} actualizado con éxito."

    except sqlite3.IntegrityError:
        return "Error: DNI/NIE ya existe."
    except sqlite3.Error as e:
        return f"Error DB al guardar paciente: {e}"
    finally:
        conn.close()

def obtener_pacientes():
    """Obtiene todos los pacientes (desencriptando los campos sensibles)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, apellidos, dni_nie, telefono_enc, direccion_enc, email_enc, notas_enc, fecha_registro FROM Pacientes ORDER BY apellidos, nombre")
    pacientes_raw = cursor.fetchall()
    conn.close()
    
    pacientes_desenc = []
    for p in pacientes_raw:
        paciente = list(p)
        paciente[4] = decrypt_field(p[4]) 
        paciente[5] = decrypt_field(p[5]) 
        paciente[6] = decrypt_field(p[6]) 
        paciente[7] = decrypt_field(p[7]) 
        pacientes_desenc.append(paciente)
        
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

def guardar_tratamiento(nombre, descripcion, precio_unitario, id_tratamiento=None):
    """Guarda o actualiza un tratamiento."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        if id_tratamiento is None:
            cursor.execute("""
                INSERT INTO Tratamientos (nombre, descripcion, precio_unitario, fecha_creacion)
                VALUES (?, ?, ?, ?)
            """, (nombre, descripcion, precio_unitario, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            conn.commit()
            return "Tratamiento creado con éxito."
        else:
            cursor.execute("""
                UPDATE Tratamientos SET nombre=?, descripcion=?, precio_unitario=?
                WHERE id=?
            """, (nombre, descripcion, precio_unitario, id_tratamiento))
            conn.commit()
            return "Tratamiento actualizado con éxito."

    except sqlite3.Error as e:
        return f"Error DB al guardar tratamiento: {e}"
    finally:
        conn.close()

def obtener_tratamientos():
    """Obtiene todos los tratamientos."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, descripcion, precio_unitario, fecha_creacion FROM Tratamientos ORDER BY nombre")
    tratamientos = cursor.fetchall()
    conn.close()
    return tratamientos

def eliminar_tratamiento(id_tratamiento):
    """Elimina un tratamiento por ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Tratamientos WHERE id=?", (id_tratamiento,))
        conn.commit()
        if cursor.rowcount > 0:
            return "Tratamiento eliminado con éxito."
        else:
            return "Tratamiento no encontrado."
    except sqlite3.Error as e:
        return f"Error DB al eliminar tratamiento: {e}"
    finally:
        conn.close()

def generar_numero_presupuesto():
    """Genera el número de presupuesto único para el año actual (e.g., 2025-001)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    año_actual = datetime.now().strftime('%Y')
    
    cursor.execute("""
        SELECT COUNT(*) FROM Presupuestos 
        WHERE strftime('%Y', fecha) = ?
    """, (año_actual,))
    
    conteo = cursor.fetchone()[0]
    siguiente_numero = conteo + 1
    
    numero_presupuesto = f"{año_actual}-{siguiente_numero:03d}" 
    conn.close()
    return numero_presupuesto

def guardar_presupuesto_completo(paciente_id, detalles, subtotal, descuento, iva_porcentaje, total, notas, numero_presupuesto=None, id_presupuesto=None):
    """Guarda o actualiza un presupuesto y sus detalles."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        if id_presupuesto is None:
            if numero_presupuesto is None:
                 return "Error: Falta el número de presupuesto para la creación." 
            
            cursor.execute("""
                INSERT INTO Presupuestos (numero_presupuesto, paciente_id, fecha, subtotal, descuento, iva_porcentaje, total, notas)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (numero_presupuesto, paciente_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
                  subtotal, descuento, iva_porcentaje, total, notas))
            id_presupuesto = cursor.lastrowid
            accion = "creado"
            
        else:
            update_num = f", numero_presupuesto='{numero_presupuesto}'" if numero_presupuesto else ""
            params = [subtotal, descuento, iva_porcentaje, total, notas, id_presupuesto]
            if numero_presupuesto:
                params.insert(-1, numero_presupuesto)

            cursor.execute(f"""
                UPDATE Presupuestos SET subtotal=?, descuento=?, iva_porcentaje=?, total=?, notas=? {update_num}
                WHERE id=?
            """, params if not numero_presupuesto else [subtotal, descuento, iva_porcentaje, total, notas, numero_presupuesto, id_presupuesto])
            accion = "actualizado"
            
            cursor.execute("DELETE FROM Presupuestos_Detalles WHERE presupuesto_id=?", (id_presupuesto,))

        for item in detalles:
            tratamiento_id, nombre_manual, cantidad, precio_unitario = item
            subtotal_detalle = cantidad * precio_unitario
            
            cursor.execute("""
                INSERT INTO Presupuestos_Detalles (presupuesto_id, tratamiento_id, nombre_manual, cantidad, precio_unitario, subtotal)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (id_presupuesto, tratamiento_id, nombre_manual, cantidad, precio_unitario, subtotal_detalle))
            
        conn.commit()
        return f"Presupuesto {numero_presupuesto or id_presupuesto} {accion} con éxito. ID: {id_presupuesto}"
        
    except sqlite3.IntegrityError as e:
        return f"Error de integridad (posible duplicado de número de presupuesto): {e}"
    except sqlite3.Error as e:
        conn.rollback()
        return f"Error DB al guardar presupuesto: {e}"
    finally:
        conn.close()

def obtener_presupuestos(id_presupuesto=None):
    """Obtiene una lista de presupuestos o uno específico con sus detalles."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if id_presupuesto:
        cursor.execute("SELECT * FROM Presupuestos WHERE id=?", (id_presupuesto,))
        presupuesto = cursor.fetchone()
        
        cursor.execute("SELECT tratamiento_id, nombre_manual, cantidad, precio_unitario, subtotal FROM Presupuestos_Detalles WHERE presupuesto_id=?", (id_presupuesto,))
        detalles = cursor.fetchall()
        
        conn.close()
        return (presupuesto, detalles)
    
    else:
        cursor.execute("""
            SELECT P.id, P.numero_presupuesto, C.nombre, C.apellidos, P.fecha, P.total
            FROM Presupuestos P JOIN Pacientes C ON P.paciente_id = C.id
            ORDER BY P.fecha DESC
        """)
        presupuestos = cursor.fetchall()
        conn.close()
        return presupuestos
# db.py (Añadir al final, junto a las funciones de Presupuestos)

def obtener_presupuesto_completo_para_pdf(presupuesto_id):
    """
    Obtiene todos los datos de un presupuesto, incluyendo los detalles y
    los datos desencriptados del paciente, necesarios para el PDF.
    Devuelve (presupuesto_data, paciente_data, detalles_list)
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Obtener datos del presupuesto
    cursor.execute("SELECT * FROM Presupuestos WHERE id=?", (presupuesto_id,))
    presupuesto_raw = cursor.fetchone()
    if not presupuesto_raw:
        conn.close()
        return None

    # 2. Obtener datos del paciente (necesitamos desencriptar)
    paciente_id = presupuesto_raw[2]
    cursor.execute("SELECT * FROM Pacientes WHERE id=?", (paciente_id,))
    paciente_raw = cursor.fetchone()
    
    if not paciente_raw:
        conn.close()
        return None

    # Desencriptar los campos del paciente para el PDF
    paciente_data = list(paciente_raw)
    
    # Índices: 4=telefono_enc, 5=direccion_enc, 6=email_enc, 7=notas_enc
    if paciente_data[4]: paciente_data[4] = decrypt_field(paciente_data[4])
    if paciente_data[5]: paciente_data[5] = decrypt_field(paciente_data[5])
    if paciente_data[6]: paciente_data[6] = decrypt_field(paciente_data[6])
    if paciente_data[7]: paciente_data[7] = decrypt_field(paciente_data[7])

    # 3. Obtener detalles
    cursor.execute("SELECT * FROM Presupuestos_Detalles WHERE presupuesto_id=?", (presupuesto_id,))
    detalles_list = cursor.fetchall()
    
    conn.close()
    
    return (presupuesto_raw, paciente_data, detalles_list)

# --- TEST SIMPLE (Ejecutar para probar la Fase 1/2) ---
if __name__ == "__main__":
    # 1. Crear directorios si no existen
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        
    print(f"Directorios creados: {DATA_DIR}/ y {BACKUP_DIR}/")
    
    # 2. Setup de clave RGPD (ya se llama dentro de get_key)
    # 3. Setup de la DB y datos de prueba
    resultado_db = setup_db()
    print(resultado_db)
    
    # 4. Comprobar desencriptación (prueba de robustez, busca por el DNI específico)
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Seleccionamos el teléfono del paciente de prueba con su DNI fijo
        dni_test = "12345678A"
        cursor.execute("SELECT telefono_enc FROM Pacientes WHERE dni_nie=?", (dni_test,))
        fila = cursor.fetchone() 
        conn.close()
        
        if fila:
            tel_blob = fila[0]
            telefono_desc = decrypt_field(tel_blob)
            print(f"Prueba de desencriptación (Teléfono del ejemplo): {telefono_desc}")
            if telefono_desc == "600123456":
                print("✅ Prueba de encriptación/desencriptación OK.")
            else:
                print("❌ Error en encriptación/desencriptación (El valor no coincide).")
        else:
            print(f"❌ No se pudo encontrar el paciente con DNI {dni_test} para la prueba de desencriptación.")
            
    except Exception as e:
        print(f"❌ Error al leer o desencriptar datos de prueba: {e}")
        
    print("\n✅ FASE 1 COMPLETA Y VERIFICADA.")

    # --- TEST DE LA FASE 2: CRUD BÁSICO ---
    print("\n--- TEST CRUD PACIENTES (Fase 2) ---")
    dni_nuevo = "X0000000R" 
    
    if validar_dni_nie(dni_nuevo):
        print(f"Resultado Creación: {guardar_paciente('Ana', 'Pérez Ruiz', dni_nuevo, '666999000', 'C/ Luna 1', 'ana@test.es', 'Notas de prueba')}")
        
    pacientes = obtener_pacientes()
    if pacientes:
        paciente_a_actualizar_id = pacientes[-1][0]
        print(f"Resultado Actualización: {guardar_paciente('Ana M.', 'Pérez Ruiz', dni_nuevo, '666999001', 'C/ Sol 2', 'ana@upd.es', 'Notas de prueba UPD', paciente_a_actualizar_id)}")

    print("\n--- TEST PRESUPUESTOS (Numeración) ---")
    num_nuevo = generar_numero_presupuesto()
    print(f"Número de Presupuesto Automático Generado: {num_nuevo}")
    
    print("\n✅ FASE 2 INICIADA Y PROBADA CON ÉXITO.")
    # --- FUNCIONES DE SEGURIDAD (FASE 3) ---

def verify_user(username, password):
    """Verifica si el nombre de usuario y la contraseña son correctos."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 🚨 CAMBIO 1: SELECCIONAR password_hash Y EL ROL
    cursor.execute("SELECT password_hash, rol FROM Usuarios WHERE username=?", (username.strip().lower(),))
    user_data = cursor.fetchone()
    conn.close()
    
    if user_data:
        # Recuperamos los datos de la tupla
        password_hash_blob = user_data[0]
        rol = user_data[1] # <-- Atributo adicional
        
        # Comprobamos la contraseña
        if bcrypt.checkpw(password.encode('utf-8'), password_hash_blob):
            # 🚨 CAMBIO 2: DEVOLVER EL ROL en caso de éxito
            return rol 
    
    # Devuelve None si el usuario no existe o la contraseña es incorrecta
    return None

def get_user_role(username):
    """Obtiene el rol del usuario."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT rol FROM Usuarios WHERE username=?", (username,))
    rol = cursor.fetchone()
    conn.close()
    return rol[0] if rol else None
# db.py (Añadir estas funciones)

def cambiar_contrasena(username, new_password):
    """Permite a un usuario cambiar su propia contraseña."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        cursor.execute("UPDATE Usuarios SET password_hash=? WHERE username=?", 
                       (hashed, username))
        conn.commit()
        return "Éxito: Contraseña cambiada correctamente."
    except Exception as e:
        return f"Error: No se pudo cambiar la contraseña. {e}"
    finally:
        conn.close()

def crear_nuevo_usuario(username, password, rol):
    """Crea un nuevo usuario administrativo o recepcionista."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        if get_user_role(username) is not None:
             return "Error: El nombre de usuario ya existe."
             
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        cursor.execute("INSERT INTO Usuarios (username, password_hash, rol) VALUES (?, ?, ?)", 
                       (username, hashed, rol))
        conn.commit()
        return f"Éxito: Usuario '{username}' creado como '{rol}'."
    except Exception as e:
        return f"Error: No se pudo crear el usuario. {e}"
    finally:
        conn.close()


def obtener_paciente_por_id(patient_id):
    """
    Obtiene todos los datos de un paciente por su ID, DESENCRIPTANDO los campos sensibles.
    Se utiliza para rellenar el formulario de edición (PatientForm).
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 1. Obtener los datos.
        # El orden debe coincidir con el desempaquetado.
        # Nota: 'dni_nie' es texto plano, el resto son BLOBs encriptados.
        cursor.execute("""
            SELECT id, nombre, apellidos, dni_nie, 
                   telefono_enc, direccion_enc, email_enc, notas_enc, fecha_registro 
            FROM Pacientes 
            WHERE id=?
        """, (patient_id,))
        data = cursor.fetchone()
        
        if data:
            # 2. Desempaquetar los datos tal como vienen de la DB
            (p_id, nombre, apellidos, dni_nie, 
             telefono_enc, direccion_enc, email_enc, notas_enc, fecha_registro) = data
            
            # 3. Desencriptar los campos BLOB (teléfono, dirección, email, notas)
            # dni_nie NO se desencripta porque se guarda como texto plano en su guardar_paciente.
            telefono_dec = decrypt_field(telefono_enc)
            direccion_dec = decrypt_field(direccion_enc)
            email_dec = decrypt_field(email_enc)
            notas_dec = decrypt_field(notas_enc)
            
            # 4. Devolver los datos en formato de diccionario para facilitar el mapeo
            # a los campos del formulario PatientForm.
            return {
                "id": p_id,
                "nombre": nombre,
                "apellidos": apellidos,
                "dni_nie": dni_nie,      # Texto plano
                "telefono": telefono_dec,
                "direccion": direccion_dec,
                "email": email_dec,
                "notas": notas_dec,
                "fecha_registro": fecha_registro
            }
        return None

    except Exception as e:
        print(f"Error al obtener y desencriptar paciente ID {patient_id}: {e}")
        return None
        
    finally:
        conn.close()
def obtener_usuarios():
    """Devuelve TODOS los usuarios de la DB sin filtros."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    usuarios = [] # Inicializar como lista vacía
    try:
        # La consulta DEBE traer 4 columnas: id, username, rol, fecha_registro
        cursor.execute("SELECT id, username, rol, fecha_registro FROM Usuarios") 
        usuarios = cursor.fetchall()
        return usuarios
    except Exception as e:
        # Si hay un error de DB, imprime el error y devuelve una lista vacía
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
# db.py

# db.py (Asegúrese de que Fernet está disponible, como en obtener_paciente_por_id)

def actualizar_paciente(id, nombre, apellidos, dni, telefono, email, direccion, notas):
    """Actualiza los datos de un paciente existente, ENCRIPTANDO los campos sensibles."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Encriptar los campos sensibles usando las utilidades existentes
        telefono_enc = encrypt_field(telefono) if telefono else None
        direccion_enc = encrypt_field(direccion) if direccion else None
        email_enc = encrypt_field(email) if email else None
        notas_enc = encrypt_field(notas) if notas else None

        # Ejecutar la actualización (usar los nombres reales de las columnas)
        cursor.execute("""
            UPDATE Pacientes 
            SET nombre=?, apellidos=?, dni_nie=?, telefono_enc=?, direccion_enc=?, email_enc=?, notas_enc=?
            WHERE id=?
        """, (
            nombre,
            apellidos,
            dni, 
            sqlite3.Binary(telefono_enc) if telefono_enc else None,
            sqlite3.Binary(direccion_enc) if direccion_enc else None,
            sqlite3.Binary(email_enc) if email_enc else None,
            sqlite3.Binary(notas_enc) if notas_enc else None,
            id
        ))
        
        conn.commit()
        return "Éxito: Datos del paciente actualizados."
    except Exception as e:
        return f"Error al actualizar paciente: {e}"
    finally:
        conn.close()