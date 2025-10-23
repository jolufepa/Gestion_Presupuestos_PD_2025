import customtkinter as ctk

# Configuración del tema
BG_COLOR = "#F5F5F5"
TEXT_COLOR = "#333333"
BUTTON_COLOR = "#4CAF50"
BUTTON_HOVER = "#45A049"
SUCCESS_COLOR = "#2ECC71"
ERROR_COLOR = "#E74C3C"

PADDING_SMALL = 5
PADDING_LARGE = 10
BUTTON_WIDTH = 150
BUTTON_HEIGHT = 32
ENTRY_WIDTH = 300
TEXTBOX_HEIGHT = 100

def initialize_fonts():
    """Inicializa las fuentes para la aplicación."""
    return {
        "FONT_LABEL": ctk.CTkFont(family="Arial", size=14),
        "FONT_ENTRY": ctk.CTkFont(family="Arial", size=12),
        "FONT_BUTTON": ctk.CTkFont(family="Arial", size=14, weight="bold"),
        "FONT_TITLE": ctk.CTkFont(family="Arial", size=20, weight="bold")
    }

def apply_theme():
    """Aplica el tema de CustomTkinter."""
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("green")