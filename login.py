
import os
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime
import hashlib
import base64
from cryptography.fernet import Fernet # Ya la tenías, pero la necesitas para guardar la licencia
from db import (
    DB_PATH, get_key, obtener_paciente_por_id, verify_user, setup_db, get_user_role, 
    obtener_pacientes, guardar_paciente, eliminar_paciente, validar_dni_nie, 
    obtener_tratamientos, guardar_tratamiento, eliminar_tratamiento,
    obtener_presupuestos, guardar_presupuesto_completo, generar_numero_presupuesto,
    cambiar_contrasena, crear_nuevo_usuario, obtener_usuarios, eliminar_usuario
)
from pdf_generator import generate_pdf
from utils import resource_path, get_application_path   

SECRET_KEY = "0tONl5rIqubrEBL1po5h6Pha1r0cIb"  # <-- Define aquí tu clave secreta
def get_key():
    """
    Devuelve la clave de encriptación secreta para Fernet.
    ¡Debe ser la misma clave que usaste para encriptar el archivo!
    """
    # PEGA AQUÍ LA CLAVE QUE GENERASTE EN EL PASO 1
    return b'WaYvAQl8Wuut0Bc8BwuZW81WJeI3TIqOQUuiQANN91s='
def generate_license_key(client_name):
        """
        Genera una clave de licencia basada en el nombre del cliente y una clave secreta.
        """
        # Combinamos el nombre del cliente con nuestra clave secreta
        combined_string = f"{client_name}{SECRET_KEY}"
        
        # Creamos un hash SHA-256 de la cadena combinada
        hash_object = hashlib.sha256(combined_string.encode())
        hex_digest = hash_object.hexdigest()
        
        # Tomamos los primeros 16 caracteres del hash y los codificamos en Base64
        # para que se vea como una clave de producto (ej: X5J9-K2P8-M4N7)
        license_key = base64.b64encode(hex_digest[:16].encode()).decode('utf-8')
        
        # Formateamos la clave para que sea más legible (grupos de 4)
        formatted_key = '-'.join([license_key[i:i+4] for i in range(0, len(license_key), 4)])
        
        return formatted_key.upper()
    
class LoginWindow:
    def __init__(self, master):
        self.master = master
        master.title("Clínica Dental - Acceso")
        master.geometry("300x200")
        master.resizable(False, False)

        # 1. Comprobar la licencia primero
        if not self.check_license():
            reg_window = tk.Toplevel(master)
            app_reg = LicenseRegistrationWindow(reg_window)
            reg_window.grab_set()
            master.wait_window(reg_window)
            
            if not self.check_license():
                master.destroy()
                return

        # 2. Si la licencia es válida, configurar la UI de login
        self.setup_login_ui()
        self.center_window()

    def setup_login_ui(self):
        """Configura los widgets de la UI de login de forma limpia."""
        # Usuario
        ttk.Label(self.master, text="Usuario:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.username_entry = ttk.Entry(self.master)
        self.username_entry.grid(row=0, column=1, padx=10, pady=10)

        # Contraseña
        ttk.Label(self.master, text="Contraseña:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.password_entry = ttk.Entry(self.master, show="*")
        self.password_entry.grid(row=1, column=1, padx=10, pady=10)

        # Botón de Acceder
        ttk.Button(self.master, text="Acceder", command=self.login).grid(row=2, column=0, columnspan=2, pady=20)
        
        # Poner el foco en el campo de usuario
        self.username_entry.focus_set()

    def center_window(self):
        """Centra la ventana en la pantalla."""
        self.master.update_idletasks()
        width = self.master.winfo_width()
        height = self.master.winfo_height()
        x = (self.master.winfo_screenwidth() // 2) - (width // 2)
        y = (self.master.winfo_screenheight() // 2) - (height // 2)
        self.master.geometry(f'{width}x{height}+{x}+{y}')

    def check_license(self):
        """Comprueba si existe un archivo de licencia válido en la carpeta del programa."""
        app_dir = get_application_path()
        license_path = os.path.join(app_dir, 'license.lic')

        print(f"DEBUG: Buscando licencia en la ruta: {license_path}")
        try:
            with open(license_path, 'rb') as f:
                encrypted_data = f.read()

            print("Archivo de licencia encontrado. Intentando descifrar...")
            cipher_suite = Fernet(get_key())
            decrypted_data = cipher_suite.decrypt(encrypted_data).decode('utf-8')

            print(f"Datos descifrados: {decrypted_data}")
            client_name, license_key = decrypted_data.split('|')

            print(f"Nombre de cliente: {client_name}, Clave: {license_key}")
            expected_key = generate_license_key(client_name)
            print(f"Clave esperada: {expected_key}")

            is_valid = license_key == expected_key
            print(f"¿La licencia es válida? {is_valid}")

            return is_valid

        except FileNotFoundError:
            print("Error: El archivo license.lic no fue encontrado.")
            return False
        except Exception as e:
            print(f"Error al verificar licencia: {e}")
            return False

    def open_main_window(self, username, rol):
        """Destruye la ventana de login y abre la ventana principal."""
        self.master.destroy() 
        main_root = tk.Tk()
        MainWindow(main_root, username, rol)
        main_root.mainloop()

    def login(self):
        """Gestiona el evento de clic en el botón de acceso."""
        username = self.username_entry.get()
        password = self.password_entry.get()

        rol = verify_user(username, password)
        if rol:
            messagebox.showinfo("Éxito", f"Bienvenido, {username} ({rol})")
            self.open_main_window(username, rol)
        else:
            messagebox.showerror("Error de Acceso", "Usuario o contraseña incorrectos.")

class MainWindow:
    def __init__(self, master, username, rol):
        self.master = master
        self.username = username
        self.rol = rol
        master.title(f"Clínica Dental - Gestión ({rol.title()})")
        
        self.notebook = ttk.Notebook(master)
        self.notebook.pack(pady=10, padx=10, expand=True, fill="both")

        self.tab_pacientes = ttk.Frame(self.notebook)
        self.tab_tratamientos = ttk.Frame(self.notebook)
        self.tab_presupuestos = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_pacientes, text='Pacientes')
        self.notebook.add(self.tab_tratamientos, text='Tratamientos')
        self.notebook.add(self.tab_presupuestos, text='Presupuestos')
        
        self.setup_pacientes_tab()
        self.setup_tratamientos_tab()
        self.setup_presupuestos_tab()
        
        # <-- MEJORA: Lógica de administración más robusta
        if self.rol and self.rol.lower() == 'administrador':
         self.setup_admin_tab()
        
        self.create_menu()
        master.geometry("1000x700") 
        master.update_idletasks()
        w = master.winfo_width()
        h = master.winfo_height()
        ws = master.winfo_screenwidth()
        hs = master.winfo_screenheight()
        x = (ws/2) - (w/2)
        y = (hs/2) - (h/2)
        master.geometry('%dx%d+%d+%d' % (w, h, x, y))

    def create_menu(self):
        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Cambiar Contraseña", command=self.open_password_change)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.master.quit)
        menubar.add_cascade(label="Archivo", menu=file_menu)
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Acerca de", command=lambda: messagebox.showinfo("Info", "Gestor de Presupuestos Dental - Versión 1.0"))
        menubar.add_cascade(label="Ayuda", menu=help_menu)

    def open_password_change(self):
        change_window = tk.Toplevel(self.master)
        ChangePasswordForm(change_window, self.username)

    # --- MÓDULO DE PACIENTES ---
    def setup_pacientes_tab(self):
        top_frame = ttk.Frame(self.tab_pacientes)
        top_frame.pack(padx=10, pady=10, fill="x")
        ttk.Button(top_frame, text="Nuevo Paciente", command=self.open_paciente_form).pack(side="left", padx=5)
        ttk.Button(top_frame, text="Editar Paciente", command=self.open_edit_patient_form).pack(side="left", padx=5)
        ttk.Button(top_frame, text="Eliminar Paciente", command=self.delete_selected_paciente).pack(side="left", padx=5)
        
        self.pacientes_tree = ttk.Treeview(self.tab_pacientes, columns=("ID", "Nombre", "Apellidos", "DNI/NIE", "Teléfono", "Email", "Registro"), show='headings')
        self.pacientes_tree.pack(padx=10, pady=5, expand=True, fill="both")
        
        self.pacientes_tree.heading("ID", text="ID", anchor="center")
        self.pacientes_tree.heading("Nombre", text="Nombre")
        self.pacientes_tree.heading("Apellidos", text="Apellidos")
        self.pacientes_tree.heading("DNI/NIE", text="DNI/NIE")
        self.pacientes_tree.heading("Teléfono", text="Teléfono")
        self.pacientes_tree.heading("Email", text="Email")
        self.pacientes_tree.heading("Registro", text="Registro")
        self.pacientes_tree.column("ID", width=30, anchor="center")
        self.pacientes_tree.column("Nombre", width=120)
        self.pacientes_tree.column("Apellidos", width=150)
        self.pacientes_tree.column("DNI/NIE", width=100, anchor="center")
        self.pacientes_tree.column("Teléfono", width=100)
        self.pacientes_tree.column("Email", width=150)
        self.pacientes_tree.column("Registro", width=100)
        
        scrollbar = ttk.Scrollbar(self.tab_pacientes, orient="vertical", command=self.pacientes_tree.yview)
        self.pacientes_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.pacientes_tree.pack_forget()
        self.pacientes_tree.pack(padx=10, pady=5, expand=True, fill="both", before=scrollbar)
        self.load_pacientes_data()

    def load_pacientes_data(self):
        for item in self.pacientes_tree.get_children():
            self.pacientes_tree.delete(item)
        pacientes = obtener_pacientes()
        for p in pacientes:
            self.pacientes_tree.insert("", "end", values=(p[0], p[1], p[2], p[3], p[4], p[6], p[8][:10])) 

    def open_paciente_form(self, paciente_id=None, data=None):
        form_window = tk.Toplevel(self.master)
        PatientForm(form_window, self.load_pacientes_data, paciente_id, data) 
        form_window.grab_set()
        self.master.wait_window(form_window)

    def open_edit_patient_form(self):
        selected_item = self.pacientes_tree.focus()
        if not selected_item:
            messagebox.showerror("Error", "Debe seleccionar un paciente para editar.")
            return
        patient_id = self.pacientes_tree.item(selected_item, 'values')[0]
        patient_data = obtener_paciente_por_id(patient_id) 
        if patient_data:
            edit_window = tk.Toplevel(self.master)
            PatientForm(edit_window, self.load_pacientes_data, paciente_id=patient_id, data=patient_data) 
        else:
            messagebox.showerror("Error", f"No se encontraron datos para el ID: {patient_id}")
              
    def delete_selected_paciente(self):
        selected_item = self.pacientes_tree.focus()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Selecciona un paciente para eliminar.")
            return
        paciente_id = self.pacientes_tree.item(selected_item, 'values')[0]
        paciente_nombre = self.pacientes_tree.item(selected_item, 'values')[1]
        if messagebox.askyesno("Confirmar Eliminación", f"¿Estás seguro de que quieres eliminar a {paciente_nombre} (ID: {paciente_id})?"):
            resultado = eliminar_paciente(paciente_id)
            messagebox.showinfo("Resultado", resultado)
            self.load_pacientes_data()

    # --- MÓDULO DE TRATAMIENTOS ---
    def setup_tratamientos_tab(self):
        top_frame = ttk.Frame(self.tab_tratamientos)
        top_frame.pack(padx=10, pady=10, fill="x")
        ttk.Button(top_frame, text="Nuevo Tratamiento", command=self.open_tratamiento_form).pack(side="left", padx=5)
        ttk.Button(top_frame, text="Editar Tratamiento", command=self.edit_selected_tratamiento).pack(side="left", padx=5)
        ttk.Button(top_frame, text="Eliminar Tratamiento", command=self.delete_selected_tratamiento).pack(side="left", padx=5)
        
        self.tratamientos_tree = ttk.Treeview(self.tab_tratamientos, columns=("ID", "Nombre", "Descripción", "Precio", "Registro"), show='headings')
        self.tratamientos_tree.pack(padx=10, pady=5, expand=True, fill="both")
        self.tratamientos_tree.heading("ID", text="ID", anchor="center")
        self.tratamientos_tree.heading("Nombre", text="Nombre")
        self.tratamientos_tree.heading("Descripción", text="Descripción")
        self.tratamientos_tree.heading("Precio", text="Precio (€)", anchor="center")
        self.tratamientos_tree.heading("Registro", text="Registro")
        self.tratamientos_tree.column("ID", width=30, anchor="center")
        self.tratamientos_tree.column("Nombre", width=150)
        self.tratamientos_tree.column("Descripción", width=300)
        self.tratamientos_tree.column("Precio", width=100, anchor="e")
        self.tratamientos_tree.column("Registro", width=100)
        self.load_tratamientos_data()

    def load_tratamientos_data(self):
        for item in self.tratamientos_tree.get_children():
            self.tratamientos_tree.delete(item)
        tratamientos = obtener_tratamientos() 
        for t in tratamientos:
            precio_formateado = f"{t[3]:.2f}"
            self.tratamientos_tree.insert("", "end", values=(t[0], t[1], t[2], precio_formateado, t[4][:10])) 

    def open_tratamiento_form(self, tratamiento_id=None, data=None):
        form_window = tk.Toplevel(self.master)
        TreatmentForm(form_window, self.load_tratamientos_data, tratamiento_id, data) 
        form_window.grab_set()
        self.master.wait_window(form_window) 

    def edit_selected_tratamiento(self):
        selected_item = self.tratamientos_tree.focus()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Selecciona un tratamiento para editar.")
            return
        data_values = self.tratamientos_tree.item(selected_item, 'values')
        tratamiento_id = data_values[0]
        data = {"id": tratamiento_id, "Nombre": data_values[1], "Descripción": data_values[2], "Precio": data_values[3].replace(',', '.')}
        self.open_tratamiento_form(tratamiento_id=tratamiento_id, data=data) 

    def delete_selected_tratamiento(self):
        selected_item = self.tratamientos_tree.focus()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Selecciona un tratamiento para eliminar.")
            return
        tratamiento_id = self.tratamientos_tree.item(selected_item, 'values')[0]
        tratamiento_nombre = self.tratamientos_tree.item(selected_item, 'values')[1]
        if messagebox.askyesno("Confirmar Eliminación", f"¿Estás seguro de que quieres eliminar el tratamiento: {tratamiento_nombre} (ID: {tratamiento_id})?"):
            resultado = eliminar_tratamiento(tratamiento_id) 
            messagebox.showinfo("Resultado", resultado)
            self.load_tratamientos_data()

    # --- MÓDULO DE PRESUPUESTOS ---
    def setup_presupuestos_tab(self):
        top_frame = ttk.Frame(self.tab_presupuestos)
        top_frame.pack(padx=10, pady=10, fill="x")
        ttk.Button(top_frame, text="Nuevo Presupuesto", command=self.open_presupuesto_form).pack(side="left", padx=5)
        ttk.Button(top_frame, text="Ver/Editar", command=self.edit_selected_presupuesto).pack(side="left", padx=5)
        ttk.Button(top_frame, text="Generar PDF", command=self.generate_pdf_selected).pack(side="left", padx=5)
        
        self.presupuestos_tree = ttk.Treeview(self.tab_presupuestos, columns=("ID", "Número", "Paciente", "Fecha", "Total"), show='headings')
        self.presupuestos_tree.pack(padx=10, pady=5, expand=True, fill="both")
        self.presupuestos_tree.heading("ID", text="ID", anchor="center")
        self.presupuestos_tree.heading("Número", text="Número", anchor="center")
        self.presupuestos_tree.heading("Paciente", text="Paciente")
        self.presupuestos_tree.heading("Fecha", text="Fecha", anchor="center")
        self.presupuestos_tree.heading("Total", text="Total (€)", anchor="center")
        self.presupuestos_tree.column("ID", width=30, anchor="center")
        self.presupuestos_tree.column("Número", width=100, anchor="center")
        self.presupuestos_tree.column("Paciente", width=350)
        self.presupuestos_tree.column("Fecha", width=100, anchor="center")
        self.presupuestos_tree.column("Total", width=100, anchor="e")
        self.load_presupuestos_data()

    def load_presupuestos_data(self):
        for item in self.presupuestos_tree.get_children():
            self.presupuestos_tree.delete(item)
        presupuestos = obtener_presupuestos() 
        for p in presupuestos:
            paciente_completo = f"{p[2]} {p[3]}"
            total_formateado = f"{p[5]:.2f}"
            self.presupuestos_tree.insert("", "end", values=(p[0], p[1], paciente_completo, p[4][:10], total_formateado))

    def open_presupuesto_form(self, presupuesto_id=None):
        form_window = tk.Toplevel(self.master)
        BudgetForm(form_window, self.load_presupuestos_data, presupuesto_id) 
        form_window.grab_set()
        self.master.wait_window(form_window) 

    def edit_selected_presupuesto(self):
        selected_item = self.presupuestos_tree.focus()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Selecciona un presupuesto para ver/editar.")
            return
        presupuesto_id = self.presupuestos_tree.item(selected_item, 'values')[0]
        self.open_presupuesto_form(presupuesto_id=presupuesto_id)

    def generate_pdf_selected(self):
        selected_item = self.presupuestos_tree.focus()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Selecciona un presupuesto para generar el PDF.")
            return
        presupuesto_id = self.presupuestos_tree.item(selected_item, 'values')[0]
        resultado = generate_pdf(presupuesto_id) 
        if resultado.startswith("Error:"):
            messagebox.showerror("Error de PDF", resultado)
        else:
            messagebox.showinfo("PDF Creado", resultado)
            try:
                os.startfile(resultado.split(": ")[1])
            except Exception:
                pass

    # <-- CORRECCIÓN: Se eliminó la primera definición duplicada de setup_admin_tab.
    # Esta es la única y correcta definición.
    def setup_admin_tab(self):
        """Configura la interfaz y la tabla para el módulo de Administración (solo visible para admins)."""
        self.tab_admin = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_admin, text='Administración')
        top_frame = ttk.Frame(self.tab_admin)
        top_frame.pack(padx=10, pady=10, fill="x")
        ttk.Button(top_frame, text="Nuevo Usuario", command=self.open_user_form).pack(side="left", padx=5)
        ttk.Button(top_frame, text="Eliminar Usuario", command=self.delete_selected_user).pack(side="left", padx=5)
        self.users_tree = ttk.Treeview(self.tab_admin, columns=("ID", "Usuario", "Rol", "Registro"), show='headings')
        self.users_tree.pack(padx=10, pady=5, expand=True, fill="both")
        self.users_tree.heading("ID", text="ID", anchor="center")
        self.users_tree.heading("Usuario", text="Usuario")
        self.users_tree.heading("Rol", text="Rol")
        self.users_tree.heading("Registro", text="Fecha Registro")
        self.users_tree.column("ID", width=30, anchor="center")
        self.users_tree.column("Usuario", width=150)
        self.users_tree.column("Rol", width=100)
        self.users_tree.column("Registro", width=150)
        self.load_users_data()

    def load_users_data(self):
        if not hasattr(self, 'users_tree'): return
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)
        usuarios = obtener_usuarios()
        for u in usuarios:
            fecha_formateada = u[3][:10] if u[3] else ""
            self.users_tree.insert("", "end", values=(u[0], u[1], u[2], fecha_formateada)) 

    def open_user_form(self):
        form_window = tk.Toplevel(self.master)
        UserForm(form_window, self.load_users_data) 
        form_window.grab_set()
        self.master.wait_window(form_window) 

    def delete_selected_user(self):
        selected_item = self.users_tree.focus()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Selecciona un usuario para eliminar.")
            return
        user_id, username = self.users_tree.item(selected_item, 'values')[0:2]
        if messagebox.askyesno("Confirmar Eliminación", f"¿Estás seguro de que quieres eliminar al usuario: {username}?"):
            resultado = eliminar_usuario(user_id)
            messagebox.showinfo("Resultado", resultado)
            self.load_users_data()

# --- FORMULARIOS MODALES ---
class PatientForm:
    def __init__(self, master, reload_callback, paciente_id=None, data=None):
        self.master = master
        self.reload_callback = reload_callback
        self.paciente_id = paciente_id
        master.title("Editar Paciente" if paciente_id else "Nuevo Paciente")
        master.geometry("400x450")
        form_frame = ttk.Frame(master, padding="10")
        form_frame.pack(expand=True, fill="both")
        fields = ["Nombre", "Apellidos", "DNI/NIE", "Teléfono", "Email", "Dirección", "Notas"]
        self.entries = {}
        for i, field in enumerate(fields):
            ttk.Label(form_frame, text=f"{field}:").grid(row=i, column=0, padx=5, pady=5, sticky="w")
            if field == "Notas":
                self.entries[field] = tk.Text(form_frame, height=3, width=30)
                self.entries[field].grid(row=i, column=1, padx=5, pady=5, sticky="w")
            else:
                self.entries[field] = ttk.Entry(form_frame, width=30)
                self.entries[field].grid(row=i, column=1, padx=5, pady=5, sticky="w")
        ttk.Button(form_frame, text="Guardar", command=self.save_patient).grid(row=len(fields), column=0, columnspan=2, pady=15)
        
        # <-- CORRECCIÓN: Cargar datos usando claves de diccionario
        if data:
            self.entries["Nombre"].insert(0, data["nombre"])
            self.entries["Apellidos"].insert(0, data["apellidos"])
            self.entries["DNI/NIE"].insert(0, data["dni_nie"])
            self.entries["Teléfono"].insert(0, data["telefono"])
            self.entries["Email"].insert(0, data["email"])
            self.entries["Dirección"].insert(0, data["direccion"])
            self.entries["Notas"].delete("1.0", tk.END)
            self.entries["Notas"].insert("1.0", data["notas"])

    def save_patient(self):
        nombre = self.entries["Nombre"].get().strip().title()
        apellidos = self.entries["Apellidos"].get().strip().title()
        dni_nie = self.entries["DNI/NIE"].get().upper().strip()
        telefono = self.entries["Teléfono"].get().strip()
        email = self.entries["Email"].get().lower().strip()
        direccion = self.entries["Dirección"].get().strip().title()
        notas = self.entries["Notas"].get("1.0", tk.END).strip()
        
        if not validar_dni_nie(dni_nie):
             messagebox.showerror("Error de Validación", "El DNI/NIE introducido no es válido.")
             return
        if not nombre or not apellidos:
             messagebox.showerror("Error de Validación", "El Nombre y Apellidos son obligatorios.")
             return

        resultado = guardar_paciente(nombre, apellidos, dni_nie, telefono, direccion, email, notas, self.paciente_id)
        if "Error:" in resultado:
            messagebox.showerror("Error al Guardar", resultado)
        else:
            messagebox.showinfo("Éxito", resultado)
            self.reload_callback() 
            self.master.destroy()

class TreatmentForm:
    def __init__(self, master, reload_callback, tratamiento_id=None, data=None):
        self.master = master; self.reload_callback = reload_callback; self.tratamiento_id = tratamiento_id
        master.title("Editar Tratamiento" if tratamiento_id else "Nuevo Tratamiento")
        master.geometry("400x350")
        form_frame = ttk.Frame(master, padding="10"); form_frame.pack(expand=True, fill="both")
        fields = ["Nombre", "Precio", "Descripción"]; self.entries = {}
        for i, field in enumerate(fields):
            ttk.Label(form_frame, text=f"{field}:").grid(row=i, column=0, padx=5, pady=5, sticky="w")
            self.entries[field] = tk.Text(form_frame, height=3, width=30) if field == "Descripción" else ttk.Entry(form_frame, width=30)
            self.entries[field].grid(row=i, column=1, padx=5, pady=5, sticky="w")
        if data: self.load_data_for_edit(data)
        ttk.Button(form_frame, text="Guardar", command=self.save_treatment).grid(row=len(fields), column=0, columnspan=2, pady=15)

    def load_data_for_edit(self, data):
        self.entries["Nombre"].insert(0, data["Nombre"])
        self.entries["Precio"].insert(0, data["Precio"])
        self.entries["Descripción"].delete("1.0", tk.END)
        self.entries["Descripción"].insert("1.0", data["Descripción"])
        
    def save_treatment(self):
        nombre = self.entries["Nombre"].get().strip().title()
        precio_str = self.entries["Precio"].get().strip().replace(',', '.')
        descripcion = self.entries["Descripción"].get("1.0", tk.END).strip()
        try:
            precio = float(precio_str)
            if precio <= 0: raise ValueError("El precio debe ser positivo.")
        except ValueError:
            messagebox.showerror("Error de Validación", "El precio debe ser un número válido mayor que cero."); return
        if not nombre:
             messagebox.showerror("Error de Validación", "El Nombre del tratamiento es obligatorio."); return
        resultado = guardar_tratamiento(nombre, descripcion, precio, self.tratamiento_id)
        if "Error:" in resultado: messagebox.showerror("Error al Guardar", resultado)
        else: messagebox.showinfo("Éxito", resultado); self.reload_callback(); self.master.destroy()

class ManualItemForm:
    def __init__(self, master, callback):
        self.master = master; self.callback = callback
        master.title("Añadir Ítem Manual"); master.geometry("350x200")
        form_frame = ttk.Frame(master, padding="10"); form_frame.pack(expand=True, fill="both")
        ttk.Label(form_frame, text="Descripción:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.desc_entry = ttk.Entry(form_frame, width=30); self.desc_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        ttk.Label(form_frame, text="Cantidad:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.cant_entry = ttk.Entry(form_frame, width=10); self.cant_entry.insert(0, "1"); self.cant_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        ttk.Label(form_frame, text="Precio Unitario (€):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.precio_entry = ttk.Entry(form_frame, width=10); self.precio_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        ttk.Button(form_frame, text="Añadir Ítem", command=self.save_item).grid(row=3, column=0, columnspan=2, pady=15)

    def save_item(self):
        descripcion = self.desc_entry.get().strip().title()
        cantidad_str = self.cant_entry.get().strip(); precio_str = self.precio_entry.get().strip().replace(',', '.')
        if not descripcion: messagebox.showerror("Error", "La descripción es obligatoria."); return
        try:
            cantidad = int(cantidad_str); precio = float(precio_str)
            if cantidad <= 0 or precio <= 0: raise ValueError
        except ValueError: messagebox.showerror("Error", "Cantidad y Precio deben ser números positivos válidos."); return
        self.callback(descripcion, cantidad, precio); self.master.destroy()

class BudgetForm:
    """Clase para la ventana modal de Creación/Edición de Presupuestos."""
    def __init__(self, master, reload_callback, presupuesto_id=None):
        self.master = master
        self.reload_callback = reload_callback
        self.presupuesto_id = presupuesto_id
        
        master.title("Editar Presupuesto" if presupuesto_id else "Nuevo Presupuesto")
        master.geometry("900x600")
        
        # Datos de la aplicación
        self.pacientes_data = self.get_pacientes_data() # Diccionario {nombre_completo: id}
        self.tratamientos_data = self.get_tratamientos_data() # Diccionario {nombre: (id, precio)}
        self.detalle_items = {} # {iid: (id_tratamiento, nombre_manual, cantidad, precio, subtotal)}
        self.detalle_counter = 0

        # Crear el contenedor principal
        main_frame = ttk.Frame(master, padding="10")
        main_frame.pack(expand=True, fill="both")
        
        # Frame 1: Cabecera (Paciente, Número, Fecha)
        header_frame = ttk.LabelFrame(main_frame, text="Datos del Presupuesto", padding="10")
        header_frame.pack(fill="x", pady=5)
        
        # Número de Presupuesto
        numero_presupuesto = generar_numero_presupuesto() if not presupuesto_id else "..."
        ttk.Label(header_frame, text="Número:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.num_label = ttk.Label(header_frame, text=numero_presupuesto, font=('Arial', 10, 'bold'))
        self.num_label.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.numero_presupuesto = numero_presupuesto

        # Selector de Paciente
        ttk.Label(header_frame, text="Paciente:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.paciente_var = tk.StringVar()
        self.paciente_combo = ttk.Combobox(header_frame, textvariable=self.paciente_var, 
                                           values=list(self.pacientes_data.keys()), state='normal', width=50)
        self.paciente_combo.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky="ew")
        # <-- ESTA ES LA LÍNEA QUE CAUSA EL ERROR. ASEGÚRATE DE QUE EL MÉTODO EXISTA.
        self.paciente_combo.bind('<KeyRelease>', self.filter_pacientes_list)
        
        # Frame 2: Detalles (Tabla)
        details_frame = ttk.LabelFrame(main_frame, text="Detalles del Presupuesto", padding="10")
        details_frame.pack(fill="both", expand=True, pady=10)
        
        self.setup_details_tree(details_frame)

        # Frame 3: Pie (Totales y Botones)
        footer_frame = ttk.Frame(main_frame)
        footer_frame.pack(fill="x", pady=5)
        
        self.setup_totals(footer_frame)
        
        # Botones de gestión del detalle
        detail_buttons_frame = ttk.Frame(details_frame)
        detail_buttons_frame.pack(fill="x", pady=5)
        
        ttk.Label(detail_buttons_frame, text="Añadir Tratamiento:").pack(side="left", padx=5)
        self.tratamiento_var = tk.StringVar()
        self.tratamiento_combo = ttk.Combobox(detail_buttons_frame, textvariable=self.tratamiento_var, 
                                               values=list(self.tratamientos_data.keys()), state='readonly', width=30)
        self.tratamiento_combo.pack(side="left", padx=5)
        ttk.Button(detail_buttons_frame, text="Añadir", command=self.add_tratamiento_to_tree).pack(side="left", padx=5)
        ttk.Button(detail_buttons_frame, text="Añadir Manual", command=self.add_manual_item).pack(side="left", padx=10)
        ttk.Button(detail_buttons_frame, text="Eliminar Línea", command=self.remove_detail_item).pack(side="right", padx=5)

        # Cargar datos si es edición
        if presupuesto_id:
            self.load_budget_data()
        
    def get_pacientes_data(self):
        """Mapea pacientes a un diccionario {nombre_completo: id_paciente}."""
        pacientes_raw = obtener_pacientes()
        return {f"{p[1]} {p[2]} (DNI: {p[3]})": p[0] for p in pacientes_raw}

    def get_tratamientos_data(self):
        """Mapea tratamientos a un diccionario {nombre: (id, precio)}."""
        tratamientos_raw = obtener_tratamientos()
        return {t[1]: (t[0], t[3]) for t in tratamientos_raw} # t[1]=nombre, t[0]=id, t[3]=precio

    def setup_details_tree(self, master):
        """Configura la tabla Treeview para los detalles del presupuesto."""
        self.details_tree = ttk.Treeview(master, 
                                          columns=("Nombre", "Cantidad", "Precio", "Subtotal"), 
                                          show='headings')
        self.details_tree.pack(expand=True, fill="both")

        self.details_tree.heading("Nombre", text="Nombre/Descripción del Item")
        self.details_tree.heading("Cantidad", text="Cant.", anchor="center")
        self.details_tree.heading("Precio", text="Precio U. (€)", anchor="e")
        self.details_tree.heading("Subtotal", text="Subtotal (€)", anchor="e")

        self.details_tree.column("Nombre", width=400)
        self.details_tree.column("Cantidad", width=70, anchor="center")
        self.details_tree.column("Precio", width=100, anchor="e")
        self.details_tree.column("Subtotal", width=100, anchor="e")
        
        self.details_tree.bind('<Delete>', lambda e: self.remove_detail_item())

    def add_tratamiento_to_tree(self):
        """Añade el tratamiento seleccionado del combobox a la tabla de detalles."""
        nombre_tratamiento = self.tratamiento_var.get()
        if not nombre_tratamiento or nombre_tratamiento not in self.tratamientos_data:
            messagebox.showwarning("Advertencia", "Selecciona un tratamiento válido.")
            return

        tratamiento_id, precio = self.tratamientos_data[nombre_tratamiento]
        cantidad = 1 # Por defecto
        subtotal = cantidad * precio
        
        iid = self.details_tree.insert("", "end", values=(nombre_tratamiento, cantidad, f"{precio:.2f}", f"{subtotal:.2f}"))
        
        self.detalle_counter += 1
        # Guardamos la información completa en el diccionario interno
        self.detalle_items[iid] = {
            "id_tratamiento": tratamiento_id, 
            "nombre_manual": nombre_tratamiento, 
            "cantidad": cantidad, 
            "precio": precio, 
            "subtotal": subtotal
        }
        self.calculate_totals()
        
    def remove_detail_item(self):
        """Elimina la línea seleccionada de la tabla de detalles."""
        selected_item = self.details_tree.focus()
        if not selected_item:
            return

        del self.detalle_items[selected_item]
        self.details_tree.delete(selected_item)
        self.calculate_totals()

    def setup_totals(self, master):
        """Configura los campos de totales, descuentos e IVA."""
        
        # Descuento
        ttk.Label(master, text="Descuento (%):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.descuento_var = tk.StringVar(value="0.0")
        self.descuento_entry = ttk.Entry(master, textvariable=self.descuento_var, width=10)
        self.descuento_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.descuento_entry.bind('<FocusOut>', lambda e: self.calculate_totals()) # Recalcular al salir del campo
        
        # IVA
        ttk.Label(master, text="IVA (%):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.iva_var = tk.StringVar(value="0.0")
        self.iva_entry = ttk.Entry(master, textvariable=self.iva_var, width=10)
        self.iva_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        self.iva_entry.bind('<FocusOut>', lambda e: self.calculate_totals())
        
        # Subtotal (Display)
        ttk.Label(master, text="Subtotal:").grid(row=0, column=2, padx=20, pady=5, sticky="w")
        self.subtotal_label = ttk.Label(master, text="0.00 €", font=('Arial', 10, 'bold'))
        self.subtotal_label.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        
        # Total (Display)
        ttk.Label(master, text="TOTAL FINAL:", font=('Arial', 12, 'bold')).grid(row=1, column=2, padx=20, pady=5, sticky="w")
        self.total_label = ttk.Label(master, text="0.00 €", font=('Arial', 12, 'bold', 'underline'), foreground="green")
        self.total_label.grid(row=1, column=3, padx=5, pady=5, sticky="w")
        
        # Botón Guardar
        ttk.Button(master, text="Guardar Presupuesto", command=self.save_budget).grid(row=0, column=4, rowspan=2, padx=30, pady=5, sticky="e")
        
        # Campos de notas
        ttk.Label(master, text="Notas:").grid(row=2, column=0, padx=5, pady=5, sticky="nw")
        self.notas_text = tk.Text(master, height=3, width=50)
        self.notas_text.grid(row=2, column=1, columnspan=3, padx=5, pady=5, sticky="ew")

        self.calculate_totals()

    def calculate_totals(self):
        """Calcula el subtotal, descuento, IVA y total del presupuesto."""
        
        subtotal = sum(item["subtotal"] for item in self.detalle_items.values())
        
        try:
            descuento_porc = float(self.descuento_var.get().replace(',', '.'))
            iva_porc = float(self.iva_var.get().replace(',', '.'))
        except ValueError:
            # Manejo de error si el usuario introduce texto en los campos de números
            self.subtotal_label.config(text="ERROR")
            self.total_label.config(text="ERROR")
            messagebox.showerror("Error", "Descuento o IVA deben ser números válidos.")
            return

        # Aplicar Descuento
        descuento_monto = subtotal * (descuento_porc / 100)
        subtotal_con_descuento = subtotal - descuento_monto
        
        # Aplicar IVA
        iva_monto = subtotal_con_descuento * (iva_porc / 100)
        total_final = subtotal_con_descuento + iva_monto
        
        # Actualizar labels
        self.subtotal_label.config(text=f"{subtotal_con_descuento:.2f} € (Desc. aplicado)")
        self.total_label.config(text=f"{total_final:.2f} €")
        
        # Guardar valores para la DB
        self.final_subtotal = subtotal # Subtotal ANTES del descuento (para DB)
        self.final_descuento = descuento_monto # Monto de descuento
        self.final_iva_porcentaje = iva_porc
        self.final_total = total_final

    def save_budget(self):
        """Recoge todos los datos, guarda el presupuesto completo en la DB, abre el PDF y pregunta si imprimir."""
        
        # --- Validaciones iniciales (sin cambios) ---
        paciente_nombre_completo = self.paciente_var.get()
        if not paciente_nombre_completo or paciente_nombre_completo not in self.pacientes_data:
            messagebox.showerror("Error", "Selecciona un paciente válido de la lista.")
            return

        if not self.detalle_items:
            messagebox.showerror("Error", "El presupuesto debe tener al menos una línea de detalle.")
            return
        
        self.calculate_totals() 
        paciente_id = self.pacientes_data[paciente_nombre_completo]
        
        detalles_list = [
            (item["id_tratamiento"], item["nombre_manual"], item["cantidad"], item["precio"]) 
            for item in self.detalle_items.values()
        ]
        
        notas = self.notas_text.get("1.0", tk.END).strip()
        
        # --- 1. Guardar en la Base de Datos ---
        resultado, presupuesto_id_guardado = guardar_presupuesto_completo(
            paciente_id=paciente_id,
            detalles=detalles_list,
            subtotal=self.final_subtotal,
            descuento=self.final_descuento,
            iva_porcentaje=self.final_iva_porcentaje,
            total=self.final_total,
            notas=notas,
            numero_presupuesto=self.numero_presupuesto,
            id_presupuesto=self.presupuesto_id
        )
        
        if "Error:" in resultado:
            messagebox.showerror("Error al Guardar", resultado)
            return
        
        # --- 2. Recargar la tabla de presupuestos ---
        self.reload_callback()
        
        # --- NUEVA LÓGICA: Generar PDF, Abrirlo y luego Preguntar si Imprimir ---
        
        # Determinar el ID del presupuesto para generar el PDF
        id_para_pdf = presupuesto_id_guardado if not self.presupuesto_id else self.presupuesto_id
        
        # Generar el PDF automáticamente
        pdf_result = generate_pdf(id_para_pdf)
        
        # Comprobar si el PDF se generó correctamente
        if pdf_result.startswith("Error:"):
            messagebox.showerror("Error de PDF", f"El presupuesto se guardó, pero hubo un error al generar el PDF:\n{pdf_result}")
        else:
            # Extraer la ruta del archivo del mensaje de éxito
            try:
                pdf_path = pdf_result.split(": ")[1]
                messagebox.showinfo("PDF Guardado", f"El presupuesto se ha guardado y generado en PDF correctamente.\nRuta: {pdf_path}")
                
                # <-- NUEVO PASO 1: Abrir el PDF automáticamente para que el usuario lo vea
                try:
                    os.startfile(pdf_path)
                except Exception as e:
                    messagebox.showwarning("Error al Abrir", f"No se pudo abrir el PDF automáticamente.\nRuta: {pdf_path}\nError: {e}")

                # <-- NUEVO PASO 2: Preguntar si desea imprimir DESPUÉS de abrirlo
                if messagebox.askyesno("Impresión", "El PDF se ha abierto en su visor. ¿Desea imprimirlo ahora?"):
                    try:
                        # os.startfile con "print" funciona principalmente en Windows.
                        if os.name == 'nt': # 'nt' es el identificador de Windows
                            os.startfile(pdf_path, "print")
                        else:
                            # En Linux o macOS, es mejor pedir al usuario que lo imprima
                            # desde su visor de PDF para evitar problemas de compatibilidad.
                            messagebox.showinfo("Información", "Por favor, use la función de imprimir de su visor de PDF.")
                    except Exception as e:
                        messagebox.showerror("Error de Impresión", f"No se pudo enviar el documento a la cola de impresión.\nError: {e}")

            except Exception:
                 messagebox.showerror("Error", "El PDF se generó, pero no se pudo obtener la ruta del archivo.")
        
        # --- FIN DE LA NUEVA LÓGICA ---
        
        # Cerrar la ventana del formulario
        self.master.destroy()

    def load_budget_data(self):
        """Carga los datos del presupuesto existente para editar."""
        presupuesto_raw, detalles_raw = obtener_presupuestos(self.presupuesto_id)
        
        if presupuesto_raw:
            # Cargar datos generales del presupuesto
            self.numero_presupuesto = presupuesto_raw['numero_presupuesto']
            self.num_label.config(text=self.numero_presupuesto)
            
            # Cargar el paciente en el combobox
            pacientes_id_map = {v:k for k,v in self.pacientes_data.items()}
            paciente_nombre = pacientes_id_map.get(presupuesto_raw['paciente_id'], "")
            self.paciente_var.set(paciente_nombre)
            
            # Cargar los totales y notas
            self.descuento_var.set(f"{presupuesto_raw['descuento']:.2f}")
            self.iva_var.set(f"{presupuesto_raw['iva_porcentaje']:.2f}")
            self.notas_text.delete("1.0", tk.END)
            self.notas_text.insert("1.0", presupuesto_raw['notas'] or "")
            
            # Cargar los detalles en la tabla
            for item in self.details_tree.get_children():
                self.details_tree.delete(item)
            
            for item in detalles_raw:
                descripcion = item['nombre_manual']
                cantidad = item['cantidad']
                precio = f"{item['precio_unitario']:.2f}"
                subtotal = f"{item['subtotal']:.2f}"
                
                iid = self.details_tree.insert("", "end", values=(descripcion, cantidad, precio, subtotal))
                
                self.detalle_items[iid] = {
                    "id_tratamiento": item['tratamiento_id'],
                    "nombre_manual": item['nombre_manual'],
                    "cantidad": item['cantidad'],
                    "precio": item['precio_unitario'],
                    "subtotal": item['subtotal']
                }
            
            self.calculate_totals()
        else:
            messagebox.showerror("Error", f"No se encontró el presupuesto con ID {self.presupuesto_id}")
            self.master.destroy()
            
    def add_manual_item(self):
        """Abre el formulario para añadir un ítem personalizado."""
        manual_window = tk.Toplevel(self.master)
        ManualItemForm(manual_window, self.insert_manual_item) 
        manual_window.grab_set()
        self.master.wait_window(manual_window)
        
    def insert_manual_item(self, descripcion, cantidad, precio):
        """Inserta el ítem manual en el treeview y en el diccionario de detalles."""
        subtotal = cantidad * precio
        
        iid = self.details_tree.insert("", "end", values=(descripcion, cantidad, f"{precio:.2f}", f"{subtotal:.2f}"))
        
        self.detalle_counter += 1
        # Guardamos la información completa: tratamiento_id es None para ítems manuales
        self.detalle_items[iid] = {
            "id_tratamiento": None, 
            "nombre_manual": descripcion, 
            "cantidad": cantidad, 
            "precio": precio, 
            "subtotal": subtotal
        }
        self.calculate_totals()

    # <-- ESTE ES EL MÉTODO QUE FALTABA. ASEGÚRATE DE QUE ESTÉ DENTRO DE LA CLASE Y CON LA INDENTACIÓN CORRECTA.
    def filter_pacientes_list(self, event):
        """Filtra la lista de pacientes en el Combobox al teclear."""
        search_term = self.paciente_var.get().lower()
        if not search_term:
            self.paciente_combo['values'] = list(self.pacientes_data.keys())
            return
            
        filtered_list = [
            name for name in self.pacientes_data.keys() 
            if search_term in name.lower()
        ]
        self.paciente_combo['values'] = filtered_list
 

class ChangePasswordForm:
    def __init__(self, master, username):
        self.master = master; self.username = username
        master.title(f"Cambiar Contraseña - {username}"); master.geometry("300x200")
        form_frame = ttk.Frame(master, padding="10"); form_frame.pack(expand=True, fill="both")
        ttk.Label(form_frame, text="Nueva Contraseña:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.new_pass_entry = ttk.Entry(form_frame, show="*", width=25); self.new_pass_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        ttk.Label(form_frame, text="Confirmar:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.confirm_pass_entry = ttk.Entry(form_frame, show="*", width=25); self.confirm_pass_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        ttk.Button(form_frame, text="Guardar", command=self.submit_change).grid(row=2, column=0, columnspan=2, pady=15)
        master.grab_set()

    def submit_change(self):
        new_pass = self.new_pass_entry.get(); confirm_pass = self.confirm_pass_entry.get()
        if new_pass != confirm_pass: messagebox.showerror("Error", "Las contraseñas no coinciden."); return
        if len(new_pass) < 6: messagebox.showerror("Error", "La contraseña debe tener al menos 6 caracteres."); return
        resultado = cambiar_contrasena(self.username, new_pass)
        if "Éxito" in resultado: messagebox.showinfo("Éxito", "Contraseña actualizada. Por favor, inicia sesión de nuevo."); self.master.destroy()
        else: messagebox.showerror("Error", resultado)

class UserForm:
    def __init__(self, master, reload_callback):
        self.master = master; self.reload_callback = reload_callback
        master.title("Nuevo Usuario"); master.geometry("300x250")
        form_frame = ttk.Frame(master, padding="10"); form_frame.pack(expand=True, fill="both")
        ttk.Label(form_frame, text="Usuario:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.user_entry = ttk.Entry(form_frame, width=25); self.user_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        ttk.Label(form_frame, text="Contraseña:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.pass_entry = ttk.Entry(form_frame, show="*", width=25); self.pass_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        ttk.Label(form_frame, text="Rol:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.rol_var = tk.StringVar(value="recepcionista")
        self.rol_combo = ttk.Combobox(form_frame, textvariable=self.rol_var, values=['admin', 'recepcionista'], state='readonly', width=22)
        self.rol_combo.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        ttk.Button(form_frame, text="Crear Usuario", command=self.save_user).grid(row=3, column=0, columnspan=2, pady=15)

    def save_user(self):
        username = self.user_entry.get().strip().lower(); password = self.pass_entry.get()
        rol_seleccionado = self.rol_var.get().strip()
        rol_a_guardar = 'Administrador' if rol_seleccionado.lower() in ['administrador', 'admin'] else 'Recepcionista'
        if not username or len(password) < 6:
             messagebox.showerror("Error", "Usuario y Contraseña (mín 6 caracteres) son obligatorios."); return
        resultado = crear_nuevo_usuario(username, password, rol_a_guardar)
        messagebox.showinfo("Resultado", resultado)
        if "Éxito" in resultado: self.reload_callback(); self.master.destroy()

class LicenseRegistrationWindow:
    def __init__(self, master):
        self.master = master
        master.title("Activación de Licencia")
        master.geometry("400x250")
        master.resizable(False, False)

        main_frame = ttk.Frame(master, padding="20")
        main_frame.pack(expand=True, fill="both")

        ttk.Label(main_frame, text="Por favor, introduce tu nombre y tu clave de licencia.", font=('Arial', 10)).pack(pady=10)
        
        ttk.Label(main_frame, text="Nombre:").pack(anchor="w")
        self.name_entry = ttk.Entry(main_frame, width=40)
        self.name_entry.pack(pady=5, fill="x")

        ttk.Label(main_frame, text="Clave de Licencia:").pack(anchor="w")
        self.key_entry = ttk.Entry(main_frame, width=40)
        self.key_entry.pack(pady=5, fill="x")

        ttk.Button(main_frame, text="Activar", command=self.activate_license).pack(pady=20)

    # DENTRO de la clase LicenseRegistrationWindow

    def activate_license(self):
        client_name = self.name_entry.get().strip()
        license_key = self.key_entry.get().strip().upper()

        if not client_name or not license_key:
            messagebox.showerror("Error", "Todos los campos son obligatorios.")
            return

        expected_key = generate_license_key(client_name)

        if license_key == expected_key:
            try:
                cipher_suite = Fernet(get_key())
                license_data = f"{client_name}|{license_key}"
                encrypted_data = cipher_suite.encrypt(license_data.encode('utf-8'))
                
                # <-- USA TU FUNCIÓN DE UTILS
                app_dir = get_application_path()
                license_path = os.path.join(app_dir, 'license.lic')
                
                print(f"DEBUG: Guardando licencia en la ruta: {license_path}")
                
                with open(license_path, 'wb') as f:
                    f.write(encrypted_data)
                
                messagebox.showinfo("Éxito", "¡Licencia activada correctamente! La aplicación se reiniciará.")
                self.master.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar la licencia: {e}")
        else:
            messagebox.showerror("Error de Activación", "El nombre o la clave de licencia son incorrectos.")

if __name__ == "__main__":
    print("Iniciando configuración de la base de datos...")
    setup_db()
    root = tk.Tk()
    
    # <-- CORRECCIÓN 3: Ahora crea la ventana de Login, que es la que controla el flujo.
    app = LoginWindow(root)
    
    root.mainloop()
