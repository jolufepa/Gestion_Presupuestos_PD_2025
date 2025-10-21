# 🦷 Gestor de Presupuestos para Clínica Dental (v1.0)

Sistema de escritorio desarrollado en Python con Tkinter y SQLite, diseñado para gestionar pacientes, tratamientos y generar presupuestos profesionales en formato PDF.

## 📋 Características Principales

* **Seguridad:** Login de usuario con encriptación de contraseña (`bcrypt`).
* **Privacidad (LOPD):** Encriptación de datos sensibles de pacientes (teléfono, dirección, email, notas).
* **Módulo Pacientes:** CRUD completo (Crear, Leer, Editar, Eliminar).
* **Módulo Tratamientos:** CRUD para la gestión del catálogo de servicios y precios.
* **Módulo Presupuestos:** Creación de presupuestos dinámicos, cálculo automático de totales (Subtotal, Descuento, IVA) y adición de ítems manuales o predefinidos.
* **Documentación:** Generación de presupuestos finales en formato PDF (`reportlab`).

## 🛠️ Instalación y Configuración

Sigue estos pasos para poner en marcha la aplicación:

### 1. Requisitos

Asegúrate de tener **Python 3.8+** instalado en tu sistema.

### 2. Entorno Virtual

Es altamente recomendado trabajar en un entorno virtual para aislar las dependencias:

```bash
python -m venv .venv
# Activar el entorno virtual (Windows)
.\.venv\Scripts\activate
# Activar el entorno virtual (Linux/macOS)
source .venv/bin/activate