import os
import tkinter as tk
from tkinter import messagebox, ttk
from db import (
    DB_PATH, obtener_paciente_por_id, verify_user, setup_db, get_user_role, 
    obtener_pacientes, guardar_paciente, eliminar_paciente, validar_dni_nie, 
    obtener_tratamientos, guardar_tratamiento, eliminar_tratamiento,
    obtener_presupuestos, guardar_presupuesto_completo, generar_numero_presupuesto,
    # Solo necesitamos obtener_pacientes y obtener_tratamientos completos, no los individuales
)
from db import cambiar_contrasena, crear_nuevo_usuario, obtener_usuarios, eliminar_usuario, generar_numero_presupuesto, guardar_presupuesto_completo, obtener_presupuestos, obtener_pacientes, obtener_tratamientos
from pdf_generator import generate_pdf
class LoginWindow:
    def __init__(self, master):
        self.master = master
        master.title("Clínica Dental - Acceso")
        master.geometry("300x200")
        master.resizable(False, False)

        # Labels
        tk.Label(master, text="Usuario:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        tk.Label(master, text="Contraseña:").grid(row=1, column=0, padx=10, pady=10, sticky="w")

        # Entries
        self.username_entry = tk.Entry(master)
        self.password_entry = tk.Entry(master, show="*")
        
        self.username_entry.grid(row=0, column=1, padx=10, pady=10)
        self.password_entry.grid(row=1, column=1, padx=10, pady=10)

        # Botón
        tk.Button(master, text="Acceder", command=self.login).grid(row=2, column=0, columnspan=2, pady=20)
        
        # Centrar la ventana (opcional)
        master.update_idletasks()
        width = master.winfo_width()
        height = master.winfo_height()
        x = (master.winfo_screenwidth() // 2) - (width // 2)
        y = (master.winfo_screenheight() // 2) - (height // 2)
        master.geometry('{}x{}+{}+{}'.format(width, height, x, y))

    def open_main_window(self, username, rol):
        """Abre la ventana principal y cierra la de login."""
        self.master.destroy() 
        
        # Creamos una nueva ventana Tkinter para la aplicación principal
        main_root = tk.Tk()
        MainWindow(main_root, username, rol)
        main_root.mainloop()

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if verify_user(username, password):
            rol = get_user_role(username)
            messagebox.showinfo("Éxito", f"Bienvenido, {username} ({rol})")
            self.open_main_window(username, rol)
        else:
            messagebox.showerror("Error de Acceso", "Usuario o contraseña incorrectos.")


class MainWindow:
    """Clase para la Ventana Principal y la gestión de módulos."""
    def __init__(self, master, username, rol):
        self.master = master
        self.username = username
        self.rol = rol
        master.title(f"Clínica Dental - Gestión ({rol})")
        master.geometry("1000x700")

        # 1. Crear el Notebook (contenedor de pestañas)
        self.notebook = ttk.Notebook(master)
        self.notebook.pack(pady=10, padx=10, expand=True, fill="both")

        # 2. Crear las Pestañas (Frames)
        self.tab_pacientes = ttk.Frame(self.notebook)
        self.tab_tratamientos = ttk.Frame(self.notebook)
        self.tab_presupuestos = ttk.Frame(self.notebook)

        # 3. Añadir las Pestañas al Notebook
        self.notebook.add(self.tab_pacientes, text='Pacientes')
        self.notebook.add(self.tab_tratamientos, text='Tratamientos')
        self.notebook.add(self.tab_presupuestos, text='Presupuestos')
        
        # 4. Inicializar Módulos Específicos
        self.setup_pacientes_tab()
        
        # Opcional: Centrar la ventana (si no lo hiciste en el login)
        master.update_idletasks()
        w = master.winfo_width()
        h = master.winfo_height()
        ws = master.winfo_screenwidth()
        hs = master.winfo_screenheight()
        x = (ws/2) - (w/2)
        y = (hs/2) - (h/2)
        master.geometry('%dx%d+%d+%d' % (w, h, x, y))
        
        # Menú de la aplicación
        self.create_menu()

    def create_menu(self):
        """Crea el menú de la aplicación para opciones de usuario y salir."""
        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Cambiar Contraseña", command=lambda: messagebox.showinfo("Info", "Funcionalidad pendiente."))
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.master.quit)
        menubar.add_cascade(label="Archivo", menu=file_menu)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Acerca de", command=lambda: messagebox.showinfo("Info", "Gestor de Presupuestos Dental - Versión 1.0"))
        menubar.add_cascade(label="Ayuda", menu=help_menu)


    # --- INICIO DEL MÓDULO DE PACIENTES (FASE 4) ---
    import tkinter as tk
from tkinter import messagebox, ttk 
from db import (
    verify_user, setup_db, get_user_role, 
    obtener_pacientes, guardar_paciente, eliminar_paciente, validar_dni_nie
    # Importaciones de Tratamientos y Presupuestos se añadirán en futuras fases
)
# ... (El resto de tu código de login.py que NO se muestra aquí, como LoginWindow) ...

# ----------------------------------------------------------------------------------
# --- CLASES DE INTERFAZ PRINCIPAL Y MÓDULOS (CRUD DE PACIENTES) ---
# ----------------------------------------------------------------------------------

class MainWindow:
    """Clase para la Ventana Principal y la gestión de módulos."""
    # login.py (CLASE MainWindow)

    def __init__(self, master, username, rol):
        self.master = master
        self.username = username
        self.rol = rol
        # Línea de depuración temporal
        messagebox.showinfo("DEBUG: Rol de Usuario", f"Rol detectado para {username}: {rol}")
        master.title(f"Clínica Dental - Gestión ({rol.title()})")
        
        # 1. Crear el Notebook (contenedor de pestañas)
        self.notebook = ttk.Notebook(master)
        self.notebook.pack(pady=10, padx=10, expand=True, fill="both")

        # 2. Crear y ASIGNAR las Pestañas (Frames) como atributos
        self.tab_pacientes = ttk.Frame(self.notebook)      # <--- LÍNEA VITAL 1
        self.tab_tratamientos = ttk.Frame(self.notebook)   # <--- LÍNEA VITAL 2
        self.tab_presupuestos = ttk.Frame(self.notebook)   # <--- LÍNEA VITAL 3

        # 3. Añadir las Pestañas al Notebook
        self.notebook.add(self.tab_pacientes, text='Pacientes')
        self.notebook.add(self.tab_tratamientos, text='Tratamientos')
        self.notebook.add(self.tab_presupuestos, text='Presupuestos')
        
        # 4. Inicializar Módulos Específicos (USAN los atributos creados en el punto 2)
        self.setup_pacientes_tab()
        self.setup_tratamientos_tab()
        self.setup_presupuestos_tab()
        
        # Lógica de administración (Soluciona el problema de visibilidad anterior)
        if self.rol == 'Administrador':
         self.setup_admin_tab()
        
        # 5. Crear el Menú
        self.create_menu()
        
        # 6. Configurar Geometría (al final)
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
        """Crea el menú de la aplicación y la pestaña de administración si el rol es 'admin'."""
        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Cambiar Contraseña", command=self.open_password_change)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.master.quit)
        menubar.add_cascade(label="Archivo", menu=file_menu)
      
     
    def open_password_change(self):
        """Abre la ventana de cambio de contraseña."""
        change_window = tk.Toplevel(self.master)
        ChangePasswordForm(change_window, self.username)

    # --- INICIO DEL MÓDULO DE PACIENTES ---
    def setup_pacientes_tab(self):
        """Configura la interfaz y la tabla para el módulo de Pacientes."""
        
        # Contenedor superior para botones y Treeview
        top_frame = ttk.Frame(self.tab_pacientes)
        top_frame.pack(padx=10, pady=10, fill="x")

        # Botones de Acción
        ttk.Button(top_frame, text="Nuevo Paciente", command=self.open_paciente_form).pack(side="left", padx=5)
        ttk.Button(top_frame, text="Editar Paciente", command=self.open_edit_patient_form).pack(side="left", padx=5)
        ttk.Button(top_frame, text="Eliminar Paciente", command=self.delete_selected_paciente).pack(side="left", padx=5)
        
        # Configurar la tabla Treeview (Lista de Pacientes)
        self.pacientes_tree = ttk.Treeview(self.tab_pacientes, 
                                           columns=("ID", "Nombre", "Apellidos", "DNI/NIE", "Teléfono", "Email", "Registro"), 
                                           show='headings')
        self.pacientes_tree.pack(padx=10, pady=5, expand=True, fill="both")
        
        # Definir encabezados y anchos
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
        
        # Añadir Scrollbar (barra de desplazamiento)
        scrollbar = ttk.Scrollbar(self.tab_pacientes, orient="vertical", command=self.pacientes_tree.yview)
        self.pacientes_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.pacientes_tree.pack_forget() # Quitamos el pack para reordenarlo
        self.pacientes_tree.pack(padx=10, pady=5, expand=True, fill="both", before=scrollbar)

        # Cargar los datos iniciales
        self.load_pacientes_data()

    def load_pacientes_data(self):
        """Carga los pacientes desde la DB y los muestra en la tabla."""
        for item in self.pacientes_tree.get_children():
            self.pacientes_tree.delete(item)
            
        pacientes = obtener_pacientes()
        
        for p in pacientes:
            # Los datos en 'p' son: [id, nombre, apellidos, dni_nie, telefono, direccion, email, notas, fecha_registro]
            self.pacientes_tree.insert("", "end", values=(p[0], p[1], p[2], p[3], p[4], p[6], p[8][:10])) 

    def open_paciente_form(self, paciente_id=None, data=None):
        """Abre la ventana de formulario para crear o editar un paciente."""
        form_window = tk.Toplevel(self.master)
        # La forma correcta de pasar los datos en la versión final sería:
        # data = obtener_paciente_por_id(paciente_id) # Esta función estaría en db.py
        
        # Como no tenemos la función obtener_paciente_por_id, pasamos None para que el formulario sepa que cargue.
        PatientForm(form_window, self.load_pacientes_data, paciente_id, data) 
        
        # Hace que la ventana de formulario se quede encima
        form_window.grab_set()
        self.master.wait_window(form_window) # Bloquea la ventana principal hasta que se cierre el formulario

    
    def delete_selected_paciente(self):
        """Elimina el paciente seleccionado."""
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
    # --- INICIO DEL MÓDULO DE TRATAMIENTOS (FASE 5) ---
    
    def setup_tratamientos_tab(self):
        """Configura la interfaz y la tabla para el módulo de Tratamientos."""
        
        # Contenedor superior para botones y Treeview
        top_frame = ttk.Frame(self.tab_tratamientos)
        top_frame.pack(padx=10, pady=10, fill="x")

        # Botones de Acción
        ttk.Button(top_frame, text="Nuevo Tratamiento", command=self.open_tratamiento_form).pack(side="left", padx=5)
        ttk.Button(top_frame, text="Editar Tratamiento", command=self.edit_selected_tratamiento).pack(side="left", padx=5)
        ttk.Button(top_frame, text="Eliminar Tratamiento", command=self.delete_selected_tratamiento).pack(side="left", padx=5)
        
        # Configurar la tabla Treeview (Lista de Tratamientos)
        self.tratamientos_tree = ttk.Treeview(self.tab_tratamientos, 
                                              columns=("ID", "Nombre", "Descripción", "Precio", "Registro"), 
                                              show='headings')
        self.tratamientos_tree.pack(padx=10, pady=5, expand=True, fill="both")
        
        # Definir encabezados y anchos
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
        
        # Cargar los datos iniciales
        self.load_tratamientos_data()

    def load_tratamientos_data(self):
        """Carga los tratamientos desde la DB y los muestra en la tabla."""
        # Limpiar la tabla existente
        for item in self.tratamientos_tree.get_children():
            self.tratamientos_tree.delete(item)
            
        # Importamos la función de db.py (Asegúrate de que está en las importaciones iniciales)
        tratamientos = obtener_tratamientos() 
        
        for t in tratamientos:
            # Los datos en 't' son: (id, nombre, descripcion, precio_unitario, fecha_creacion)
            # Formateamos el precio para que se vea bien
            precio_formateado = f"{t[3]:.2f}"
            self.tratamientos_tree.insert("", "end", values=(t[0], t[1], t[2], precio_formateado, t[4][:10])) 

    def open_tratamiento_form(self, tratamiento_id=None, data=None):
        """Abre la ventana de formulario para crear o editar un tratamiento."""
        form_window = tk.Toplevel(self.master)
        # Usamos la nueva clase TreatmentForm
        TreatmentForm(form_window, self.load_tratamientos_data, tratamiento_id, data) 
        
        form_window.grab_set()
        self.master.wait_window(form_window) 

    def edit_selected_tratamiento(self):
        """Abre el formulario con los datos del tratamiento seleccionado para editar."""
        selected_item = self.tratamientos_tree.focus()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Selecciona un tratamiento para editar.")
            return

        # Obtenemos todos los valores de la fila seleccionada
        data_values = self.tratamientos_tree.item(selected_item, 'values')
        tratamiento_id = data_values[0]
        
        # Pasamos los datos que ya están en la tabla a la ventana del formulario
        data = {
            "id": tratamiento_id,
            "Nombre": data_values[1],
            "Descripción": data_values[2],
            "Precio": data_values[3].replace(',', '.') # Convertir a formato numérico (float)
        }
        
        self.open_tratamiento_form(tratamiento_id=tratamiento_id, data=data) 

    def delete_selected_tratamiento(self):
        """Elimina el tratamiento seleccionado."""
        selected_item = self.tratamientos_tree.focus()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Selecciona un tratamiento para eliminar.")
            return

        tratamiento_id = self.tratamientos_tree.item(selected_item, 'values')[0]
        tratamiento_nombre = self.tratamientos_tree.item(selected_item, 'values')[1]
        
        if messagebox.askyesno("Confirmar Eliminación", f"¿Estás seguro de que quieres eliminar el tratamiento: {tratamiento_nombre} (ID: {tratamiento_id})?"):
            # Importamos la función de db.py (Asegúrate de que está en las importaciones iniciales)
            resultado = eliminar_tratamiento(tratamiento_id) 
            messagebox.showinfo("Resultado", resultado)
            self.load_tratamientos_data() # Recargar la tabla        
    # --- INICIO DEL MÓDULO DE PRESUPUESTOS (FASE 6) ---

    def setup_presupuestos_tab(self):
        """Configura la interfaz y la tabla para el módulo de Presupuestos."""
        
        # Contenedor superior para botones
        top_frame = ttk.Frame(self.tab_presupuestos)
        top_frame.pack(padx=10, pady=10, fill="x")

        # Botones de Acción
        ttk.Button(top_frame, text="Nuevo Presupuesto", command=self.open_presupuesto_form).pack(side="left", padx=5)
        ttk.Button(top_frame, text="Ver/Editar", command=self.edit_selected_presupuesto).pack(side="left", padx=5)
        ttk.Button(top_frame, text="Generar PDF", command=self.generate_pdf_selected).pack(side="left", padx=5)
        
        # Configurar la tabla Treeview (Lista de Presupuestos)
        self.presupuestos_tree = ttk.Treeview(self.tab_presupuestos, 
                                              columns=("ID", "Número", "Paciente", "Fecha", "Total"), 
                                              show='headings')
        self.presupuestos_tree.pack(padx=10, pady=5, expand=True, fill="both")
        
        # Definir encabezados y anchos
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
        
        # Cargar los datos iniciales
        self.load_presupuestos_data()

    def load_presupuestos_data(self):
        """Carga los presupuestos desde la DB y los muestra en la tabla."""
        for item in self.presupuestos_tree.get_children():
            self.presupuestos_tree.delete(item)
            
        # obtener_presupuestos devuelve: (id, numero, nombre_paciente, apellidos_paciente, fecha, total)
        presupuestos = obtener_presupuestos() 
        
        for p in presupuestos:
            paciente_completo = f"{p[2]} {p[3]}" # Nombre + Apellidos
            total_formateado = f"{p[5]:.2f}"
            self.presupuestos_tree.insert("", "end", values=(p[0], p[1], paciente_completo, p[4][:10], total_formateado)) 
    def open_presupuesto_form(self, presupuesto_id=None):
        """Abre la ventana de formulario para crear o editar un presupuesto."""
        form_window = tk.Toplevel(self.master)
        
        # Pasamos las funciones de recarga y las funciones de obtención de datos para los Combobox
        BudgetForm(form_window, self.load_presupuestos_data, presupuesto_id) 
        
        form_window.grab_set()
        self.master.wait_window(form_window) 

    def edit_selected_presupuesto(self):
        """Abre el formulario con los datos del presupuesto seleccionado para editar."""
        selected_item = self.presupuestos_tree.focus()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Selecciona un presupuesto para ver/editar.")
            return

        presupuesto_id = self.presupuestos_tree.item(selected_item, 'values')[0]
        self.open_presupuesto_form(presupuesto_id=presupuesto_id)
    def generate_pdf_selected(self):
        """Genera el PDF del presupuesto seleccionado."""
        selected_item = self.presupuestos_tree.focus()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Selecciona un presupuesto para generar el PDF.")
            return

        presupuesto_id = self.presupuestos_tree.item(selected_item, 'values')[0]
        
        # Llamar a la función del generador de PDF
        resultado = generate_pdf(presupuesto_id) 
        
        # Muestra el resultado (éxito o error)
        if resultado.startswith("Error:"):
            messagebox.showerror("Error de PDF", resultado)
        else:
            messagebox.showinfo("PDF Creado", resultado)
            
            # Opcional: Abrir el PDF automáticamente (requiere la librería 'os')
            try:
                # Esto es útil para el usuario
                os.startfile(resultado.split(": ")[1])
            except Exception:
                pass # Puede fallar en Linux/Mac, ignoramos el error    
    # NOTA: La eliminación de presupuestos no es estándar en un CRUD por motivos contables.
    # Se deja pendiente si es requerida la función de DELETE.
    def setup_admin_tab(self):
        """Configura la interfaz y la tabla para el módulo de Administración (solo visible para admins)."""
        
        self.tab_admin = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_admin, text='Administración')

        top_frame = ttk.Frame(self.tab_admin)
        top_frame.pack(padx=10, pady=10, fill="x")

        ttk.Button(top_frame, text="Nuevo Usuario", command=self.open_user_form).pack(side="left", padx=5)
        ttk.Button(top_frame, text="Eliminar Usuario", command=self.delete_selected_user).pack(side="left", padx=5)
        
        self.users_tree = ttk.Treeview(self.tab_admin, 
                                           columns=("ID", "Usuario", "Rol", "Registro"), 
                                           show='headings')
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



    # login.py (dentro de la clase MainWindow)

    def load_users_data(self):
        """Carga los usuarios desde la DB y los muestra en la tabla."""
        
        # 1. Limpiar la tabla existente
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)
            
        # 2. Obtener todos los usuarios
        usuarios = obtener_usuarios() 
        print(f"DEBUG: Usuarios obtenidos de la DB: {len(usuarios)}")
        
        # 3. Insertar en la tabla
        for u in usuarios:
            fecha_registro = u[3]
            
            # Verificación y Formateo (CORRECTO)
            if fecha_registro is None:
                fecha_formateada = "" 
            else:
                fecha_formateada = fecha_registro[:10]
            
            # 🚨 CORRECCIÓN FINAL: Usar la variable formateada en la inserción
            self.users_tree.insert("", "end", values=(u[0], u[1], u[2], fecha_formateada)) 
            
        print(f"DEBUG: Elementos insertados en Treeview: {len(self.users_tree.get_children())}")
        self.master.update_idletasks()

    def open_user_form(self):
        """Abre el formulario para crear un nuevo usuario."""
        form_window = tk.Toplevel(self.master)
        UserForm(form_window, self.load_users_data) 
        form_window.grab_set()
        self.master.wait_window(form_window) 

    def delete_selected_user(self):
        """Elimina el usuario seleccionado."""
        selected_item = self.users_tree.focus()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Selecciona un usuario para eliminar.")
            return

        user_id, username = self.users_tree.item(selected_item, 'values')[0:2]
        
        if messagebox.askyesno("Confirmar Eliminación", f"¿Estás seguro de que quieres eliminar al usuario: {username}?"):
            resultado = eliminar_usuario(user_id)
            messagebox.showinfo("Resultado", resultado)
            self.load_users_data()
    # login.py (Dentro de la clase MainWindow)

    def open_edit_patient_form(self):
        """
        Obtiene el ID del paciente seleccionado y abre el formulario de edición.
        Este es el 'callback' que el botón está buscando.
        """
        selected_item = self.pacientes_tree.focus()
        if not selected_item:
            messagebox.showerror("Error", "Debe seleccionar un paciente para editar.")
            return

        # 1. Obtener el ID del paciente (Se asume que el ID es la primera columna)
        patient_id = self.pacientes_tree.item(selected_item, 'values')[0]
        
        # 2. Llamar a la función de DB para obtener los datos del paciente (DESENCRIPTADOS)
        patient_data = obtener_paciente_por_id(patient_id) 
        
        if patient_data:
            # 3. Abrir la ventana de edición, pasando los datos del paciente y la función de recarga
            edit_window = tk.Toplevel(self.master)
            # Reutilizar PatientForm para edición: pasar el callback, patient_id y los datos cargados
            PatientForm(edit_window, self.load_pacientes_data, paciente_id=patient_id, data=patient_data) 
        else:
            messagebox.showerror("Error", f"No se encontraron datos para el ID: {patient_id}")              
class PatientForm:
    """Clase para la ventana modal de Creación/Edición de Pacientes."""
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

        # Botón Guardar
        ttk.Button(form_frame, text="Guardar", command=self.save_patient).grid(row=len(fields), column=0, columnspan=2, pady=15)

        # Si es edición, cargar datos
        if data:
            # 🚨 CORRECCIÓN CLAVE: Rellenar los campos con los datos desencriptados
            # data debe ser una tupla con 7 elementos: 
            # (id, nombre, apellidos, dni, telefono, email, registro)
            
            # Mapeamos los campos del formulario a las posiciones de la tupla 'data'
            # (El registro se excluye del formulario de edición)
            
            campos_y_datos = {
                "Nombre": data[1],
                "Apellidos": data[2],
                "DNI/NIE": data[3], # DNI/NIE (desencriptado)
                "Teléfono": data[4], # Teléfono (desencriptado)
                "Email": data[5],    # Email (desencriptado)
                "Dirección": "PENDIENTE_DE_CARGAR", # Asumiendo que 'Dirección' y 'Notas' no vienen en la tupla actual.
                "Notas": "PENDIENTE_DE_CARGAR" # Se necesita un campo para NOTAS en la DB si se usa.
            }

            for field, value in campos_y_datos.items():
                if field == "Notas":
                    # Para el campo Text (Notas)
                    self.entries[field].delete("1.0", tk.END)
                    self.entries[field].insert("1.0", value)
                elif value != "PENDIENTE_DE_CARGAR":
                    # Para los campos Entry
                    self.entries[field].delete(0, tk.END)
                    self.entries[field].insert(0, value)

    def save_patient(self):
        """Recoge los datos del formulario y llama a la función de DB para guardar/actualizar."""
        # 🚨 CAMBIOS AQUÍ: Aplicar .title() y .upper() para estandarizar
        nombre = self.entries["Nombre"].get().strip().title()       # Primera letra en mayúscula
        apellidos = self.entries["Apellidos"].get().strip().title() # Primera letra en mayúscula
        dni_nie = self.entries["DNI/NIE"].get().upper().strip()     # Todo en mayúsculas
        telefono = self.entries["Teléfono"].get().strip()
        email = self.entries["Email"].get().lower().strip()         # Todo en minúsculas (estándar para emails)
        direccion = self.entries["Dirección"].get().strip().title() # Primera letra en mayúscula
        notas = self.entries["Notas"].get("1.0", tk.END).strip()
        
        # Validación mínima 
        if not validar_dni_nie(dni_nie):
             messagebox.showerror("Error de Validación", "El DNI/NIE introducido no es válido.")
             return
             
        if not nombre or not apellidos:
             messagebox.showerror("Error de Validación", "El Nombre y Apellidos son obligatorios.")
             return

        # Llamar a la función de la DB
        resultado = guardar_paciente(nombre, apellidos, dni_nie, telefono, direccion, email, notas, self.paciente_id)
        
        if "Error:" in resultado:
            messagebox.showerror("Error al Guardar", resultado)
        else:
            messagebox.showinfo("Éxito", resultado)
            self.reload_callback() 
            self.master.destroy()
            
class TreatmentForm:
    """Clase para la ventana modal de Creación/Edición de Tratamientos."""
    def __init__(self, master, reload_callback, tratamiento_id=None, data=None):
        self.master = master
        self.reload_callback = reload_callback
        self.tratamiento_id = tratamiento_id
        master.title("Editar Tratamiento" if tratamiento_id else "Nuevo Tratamiento")
        master.geometry("400x350")
        
        form_frame = ttk.Frame(master, padding="10")
        form_frame.pack(expand=True, fill="both")
        
        fields = ["Nombre", "Precio", "Descripción"]
        self.entries = {}
        
        for i, field in enumerate(fields):
            ttk.Label(form_frame, text=f"{field}:").grid(row=i, column=0, padx=5, pady=5, sticky="w")
            if field == "Descripción":
                self.entries[field] = tk.Text(form_frame, height=3, width=30)
                self.entries[field].grid(row=i, column=1, padx=5, pady=5, sticky="w")
            else:
                self.entries[field] = ttk.Entry(form_frame, width=30)
                self.entries[field].grid(row=i, column=1, padx=5, pady=5, sticky="w")
        
        # Si es edición, cargar datos
        if data:
            self.load_data_for_edit(data)

        # Botón Guardar
        ttk.Button(form_frame, text="Guardar", command=self.save_treatment).grid(row=len(fields), column=0, columnspan=2, pady=15)

    def load_data_for_edit(self, data):
        """Carga los datos del tratamiento en los campos del formulario."""
        self.entries["Nombre"].insert(0, data["Nombre"])
        self.entries["Precio"].insert(0, data["Precio"])
        # Para el widget Text, usamos delete y insert
        self.entries["Descripción"].delete("1.0", tk.END)
        self.entries["Descripción"].insert("1.0", data["Descripción"])
        
    def save_treatment(self):
        """Recoge los datos del formulario y llama a la función de DB para guardar/actualizar."""
        # 🚨 CAMBIOS AQUÍ: Aplicar .title() para estandarizar
        nombre = self.entries["Nombre"].get().strip().title()
        precio_str = self.entries["Precio"].get().strip().replace(',', '.')
        descripcion = self.entries["Descripción"].get("1.0", tk.END).strip() # Las descripciones largas NO suelen llevar title()
        
        # Validación
        try:
            precio = float(precio_str)
            if precio <= 0:
                raise ValueError("El precio debe ser positivo.")
        except ValueError:
            messagebox.showerror("Error de Validación", "El precio debe ser un número válido mayor que cero.")
            return

        if not nombre:
             messagebox.showerror("Error de Validación", "El Nombre del tratamiento es obligatorio.")
             return

        # Llamar a la función de la DB
        resultado = guardar_tratamiento(nombre, descripcion, precio, self.tratamiento_id)
        
        if "Error:" in resultado:
            messagebox.showerror("Error al Guardar", resultado)
        else:
            messagebox.showinfo("Éxito", resultado)
            self.reload_callback() # Recargar la tabla
 
class ManualItemForm:
    """Clase para la ventana modal de adición de un ítem manual a un presupuesto."""
    def __init__(self, master, callback):
        self.master = master
        self.callback = callback
        master.title("Añadir Ítem Manual")
        master.geometry("350x200")
        
        form_frame = ttk.Frame(master, padding="10")
        form_frame.pack(expand=True, fill="both")
        
        ttk.Label(form_frame, text="Descripción:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.desc_entry = ttk.Entry(form_frame, width=30)
        self.desc_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(form_frame, text="Cantidad:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.cant_entry = ttk.Entry(form_frame, width=10)
        self.cant_entry.insert(0, "1") # Valor por defecto
        self.cant_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(form_frame, text="Precio Unitario (€):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.precio_entry = ttk.Entry(form_frame, width=10)
        self.precio_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        ttk.Button(form_frame, text="Añadir Ítem", command=self.save_item).grid(row=3, column=0, columnspan=2, pady=15)

    def save_item(self):
        """Valida y devuelve los datos al formulario principal."""
        # 🚨 CAMBIOS AQUÍ: Aplicar .title() a la descripción manual
        descripcion = self.desc_entry.get().strip().title() 
        cantidad_str = self.cant_entry.get().strip()
        precio_str = self.precio_entry.get().strip().replace(',', '.')
        
        if not descripcion:
            messagebox.showerror("Error", "La descripción es obligatoria.")
            return

        try:
            cantidad = int(cantidad_str)
            precio = float(precio_str)
            if cantidad <= 0 or precio <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Cantidad y Precio deben ser números positivos válidos.")
            return

        # Llama al callback del BudgetForm para añadirlo a la tabla
        self.callback(descripcion, cantidad, precio)
        self.master.destroy()
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
        """Recoge todos los datos, guarda el presupuesto completo en la DB y gestiona el PDF."""
        
        # ... (VALIDACIONES EXISTENTES) ...
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
        
        # 1. GUARDA EN DB
        resultado = guardar_presupuesto_completo(
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
        
        # Éxito al guardar
        messagebox.showinfo("Éxito", resultado)
        self.reload_callback()
        
        # 2. GESTIÓN DEL PDF
        if messagebox.askyesno("Generación de PDF", "¿Deseas generar e imprimir el PDF del presupuesto ahora?"):
            
            # Si es un nuevo presupuesto, necesitamos el ID de la base de datos
            if not self.presupuesto_id:
                # Obtenemos el ID del presupuesto recién creado para generar el PDF
                import sqlite3
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM Presupuestos ORDER BY id DESC LIMIT 1")
                new_id = cursor.fetchone()[0]
                conn.close()
                presupuesto_a_generar = new_id
            else:
                presupuesto_a_generar = self.presupuesto_id
                
            pdf_result = generate_pdf(presupuesto_a_generar)
            
            if pdf_result.startswith("Error:"):
                 messagebox.showerror("Error de PDF", pdf_result)
            else:
                messagebox.showinfo("PDF Creado", pdf_result)
                try:
                    # Mostrar el PDF al usuario
                    import os
                    os.startfile(pdf_result.split(": ")[1])
                except Exception:
                    messagebox.showwarning("Advertencia", "No se pudo abrir el PDF automáticamente. Revise la carpeta 'data/presupuestos_pdf'.")
        
        self.master.destroy()

    def load_budget_data(self):
        """Carga los datos del presupuesto existente para edición (PENDIENTE)."""
        # 🚨 Este es un paso avanzado. Por ahora, solo cargaremos el número y el paciente.
        presupuesto_raw, detalles_raw = obtener_presupuestos(self.presupuesto_id)
        
        if presupuesto_raw:
            self.numero_presupuesto = presupuesto_raw[1] # Número de presupuesto
            self.num_label.config(text=self.numero_presupuesto)
            
            # (Aquí iría la lógica para buscar el paciente_id por ID y cargar el combobox)
            # Simplificamos buscando al paciente de ejemplo por el ID
            pacientes_id_map = {v:k for k,v in self.pacientes_data.items()}
            paciente_nombre = pacientes_id_map.get(presupuesto_raw[2], "")
            self.paciente_var.set(paciente_nombre)
            
            # Cargar los totales
            self.descuento_var.set(f"{presupuesto_raw[5]:.2f}")
            self.iva_var.set(f"{presupuesto_raw[6]:.2f}")
            self.notas_text.delete("1.0", tk.END)
            self.notas_text.insert("1.0", presupuesto_raw[8] or "")
            
            # Cargar los detalles
            # Este paso es complejo y requiere formateo específico del Treeview
            
            self.calculate_totals() # Recalcular con los valores cargados
        else:
            messagebox.showerror("Error", f"No se encontró el presupuesto con ID {self.presupuesto_id}")
            self.master.destroy()            
    def add_manual_item(self):
        """Abre el formulario para añadir un ítem personalizado."""
        manual_window = tk.Toplevel(self.master)
        # Pasamos la función 'insert_manual_item' como callback
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
    """Ventana para que un usuario cambie su propia contraseña."""
    def __init__(self, master, username):
        self.master = master
        self.username = username
        master.title(f"Cambiar Contraseña - {username}")
        master.geometry("300x200")
        
        form_frame = ttk.Frame(master, padding="10")
        form_frame.pack(expand=True, fill="both")

        ttk.Label(form_frame, text="Nueva Contraseña:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.new_pass_entry = ttk.Entry(form_frame, show="*", width=25)
        self.new_pass_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(form_frame, text="Confirmar:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.confirm_pass_entry = ttk.Entry(form_frame, show="*", width=25)
        self.confirm_pass_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        ttk.Button(form_frame, text="Guardar", command=self.submit_change).grid(row=2, column=0, columnspan=2, pady=15)
        master.grab_set()

    def submit_change(self):
        new_pass = self.new_pass_entry.get()
        confirm_pass = self.confirm_pass_entry.get()

        if new_pass != confirm_pass:
            messagebox.showerror("Error", "Las contraseñas no coinciden.")
            return
        if len(new_pass) < 6:
            messagebox.showerror("Error", "La contraseña debe tener al menos 6 caracteres.")
            return

        resultado = cambiar_contrasena(self.username, new_pass)
        
        if "Éxito" in resultado:
            messagebox.showinfo("Éxito", "Contraseña actualizada. Por favor, inicia sesión de nuevo.")
            self.master.destroy()
            # Opcional: Forzar cierre de la ventana principal para que el usuario se re-autentique
        else:
            messagebox.showerror("Error", resultado)
    def setup_admin_tab(self):
        """Configura la interfaz y la tabla para el módulo de Administración (solo visible para admins)."""
        
        self.tab_admin = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_admin, text='Administración')

        top_frame = ttk.Frame(self.tab_admin)
        top_frame.pack(padx=10, pady=10, fill="x")

        ttk.Button(top_frame, text="Nuevo Usuario", command=self.open_user_form).pack(side="left", padx=5)
        ttk.Button(top_frame, text="Eliminar Usuario", command=self.delete_selected_user).pack(side="left", padx=5)
        
        self.users_tree = ttk.Treeview(self.tab_admin, 
                                           columns=("ID", "Usuario", "Rol", "Registro"), 
                                           show='headings')
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
        """Carga los usuarios desde la DB y los muestra en la tabla."""
        if not hasattr(self, 'users_tree'): return

        for item in self.users_tree.get_children():
            self.users_tree.delete(item)
            
        usuarios = obtener_usuarios()
        
        for u in usuarios:
            self.users_tree.insert("", "end", values=(u[0], u[1], u[2], u[3][:10])) 

    def open_user_form(self):
        """Abre el formulario para crear un nuevo usuario."""
        form_window = tk.Toplevel(self.master)
        UserForm(form_window, self.load_users_data) 
        form_window.grab_set()
        self.master.wait_window(form_window) 

    def delete_selected_user(self):
        """Elimina el usuario seleccionado."""
        selected_item = self.users_tree.focus()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Selecciona un usuario para eliminar.")
            return

        user_id, username = self.users_tree.item(selected_item, 'values')[0:2]
        
        if messagebox.askyesno("Confirmar Eliminación", f"¿Estás seguro de que quieres eliminar al usuario: {username}?"):
            resultado = eliminar_usuario(user_id)
            messagebox.showinfo("Resultado", resultado)
            self.load_users_data()
class UserForm:
    """Clase para la ventana modal de Creación de Usuarios."""
    def __init__(self, master, reload_callback):
        self.master = master
        self.reload_callback = reload_callback
        master.title("Nuevo Usuario")
        master.geometry("300x250")
        
        form_frame = ttk.Frame(master, padding="10")
        form_frame.pack(expand=True, fill="both")
        
        # Usuario
        ttk.Label(form_frame, text="Usuario:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.user_entry = ttk.Entry(form_frame, width=25)
        self.user_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Contraseña
        ttk.Label(form_frame, text="Contraseña:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.pass_entry = ttk.Entry(form_frame, show="*", width=25)
        self.pass_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # Rol
        ttk.Label(form_frame, text="Rol:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.rol_var = tk.StringVar(value="recepcionista")
        self.rol_combo = ttk.Combobox(form_frame, textvariable=self.rol_var, 
                                     values=['admin', 'recepcionista'], state='readonly', width=22)
        self.rol_combo.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Button(form_frame, text="Crear Usuario", command=self.save_user).grid(row=3, column=0, columnspan=2, pady=15)

    # login.py (Dentro de la clase UserForm)

    def save_user(self):
        username = self.user_entry.get().strip().lower() 
        password = self.pass_entry.get()
        
        rol_seleccionado = self.rol_var.get().strip() # Obtiene el valor exacto del Combobox
        
        # 🚨 CORRECCIÓN CLAVE: Estandarizar el rol antes de guardar
        # Si el ComboBox tiene "admin" o "recepcionista" en minúsculas,
        # lo convertimos a "Administrador" o "Recepcionista" (con mayúscula inicial).
        if rol_seleccionado.lower() == 'administrador' or rol_seleccionado.lower() == 'admin':
            rol_a_guardar = 'Administrador'
        elif rol_seleccionado.lower() == 'recepcionista':
            rol_a_guardar = 'Recepcionista'
        else:
            rol_a_guardar = rol_seleccionado # En caso de otros roles
            
        if not username or len(password) < 6:
             messagebox.showerror("Error", "Usuario y Contraseña (mín 6 caracteres) son obligatorios.")
             return

        resultado = crear_nuevo_usuario(username, password, rol_a_guardar) # Usar el rol estandarizado
        
        messagebox.showinfo("Resultado", resultado)
        
        if "Éxito" in resultado:
            self.reload_callback()
            self.master.destroy()                           
if __name__ == "__main__":
    # 1. Configurar la DB (crea tablas y usuario 'admin')
    print("Iniciando configuración de la base de datos...")
    setup_db()
    
    # 2. Iniciar la aplicación de login
    root = tk.Tk()
    app = LoginWindow(root)
    root.mainloop()