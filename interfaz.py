import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import time
from Avility.avility import silversumit_facturacion
from Medicaid.medicaid import medicaid_facturacion
from PIL import Image, ImageTk  # si tu imagen es JPG/PNG
from cryptography.fernet import Fernet
import io
import sys
import os
import subprocess
import sys


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def save_encrypted_excel(df, path, fernet):
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False)
    encrypted_data = fernet.encrypt(buffer.getvalue())

    with open(path, "wb") as file:
        file.write(encrypted_data)


KEY = b'HzzXD8zy3oXBb-kNV_S-ElF0631LsAMzWdHh1wZOiLw='
f = Fernet(KEY)
def load_encrypted_excel(path):
    with open(path, "rb") as file:
        encrypted_data = file.read()
    decrypted_data = f.decrypt(encrypted_data)
    return pd.read_excel(io.BytesIO(decrypted_data))

DF_AVILITY = load_encrypted_excel(resource_path("avility-Usuarios.dat"))
DF_MEDICAID = load_encrypted_excel(resource_path("medicaid-Usuarios.dat"))
DF_USUARIO_APP = load_encrypted_excel(resource_path("usuarios_APP.dat"))

def preguntar_modificar(usuario_app, seguro):

    import customtkinter as ctk
    from tkinter import messagebox
    import os
    from PIL import Image

    SEGUROS = {
        "medicaid": {
            "archivo": "medicaid-Usuarios.dat",
            "df": "DF_MEDICAID"
        },
        "avility": {
            "archivo": "avility-Usuarios.dat",
            "df": "DF_AVILITY"
        }
    }

    BG_COLOR = "#f7f7f7"

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    IMAGEN_FILE = os.path.join(BASE_DIR, "Spectrum.jpg")

    # -------- VENTANA CONFIRMACION --------
    confirm = ctk.CTkToplevel()
    confirm.title("Confirmación")
    centrar_ventana(confirm, 360, 180)
    confirm.configure(fg_color=BG_COLOR)

    confirm.grab_set()
    confirm.focus()

    cont = ctk.CTkFrame(confirm, fg_color=BG_COLOR)
    cont.pack(expand=True)

    ctk.CTkLabel(
        cont,
        text=f"¿Quieres modificar tus credenciales de {seguro}?",
        font=("Segoe UI", 14, "bold"),
        text_color="black"
    ).pack(pady=(30,20))

    # ---------------- SI ----------------
    def si():

        global DF_MEDICAID, DF_AVILITY

        ventana = ctk.CTkToplevel()
        ventana.title(f"Credenciales {seguro}")
        centrar_ventana(ventana, 720, 420)
        ventana.configure(fg_color=BG_COLOR)

        frame = ctk.CTkFrame(ventana, fg_color=BG_COLOR)
        frame.pack(fill="both", expand=True, padx=30, pady=25)

        col_izq = ctk.CTkFrame(frame, fg_color=BG_COLOR)
        col_izq.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(
            col_izq,
            text=f"Gestión de credenciales {seguro}",
            font=("Segoe UI", 18, "bold"),
            text_color="black"
        ).pack(pady=(0,20))

        confirm.destroy()

        ctk.CTkLabel(
            col_izq,
            text=f"Usuario App: {usuario_app}",
            font=("Segoe UI", 13),
            text_color="black"
        ).pack(pady=(0,15))

        cambiar_usuario = ctk.BooleanVar(value=False)
        cambiar_contrasena = ctk.BooleanVar(value=False)

        ctk.CTkCheckBox(
            col_izq,
            text="Modificar usuario",
            variable=cambiar_usuario
        ).pack(anchor="w")

        entry_usuario = ctk.CTkEntry(col_izq, width=260)
        entry_usuario.pack(pady=(5,15))

        ctk.CTkCheckBox(
            col_izq,
            text="Modificar contraseña",
            variable=cambiar_contrasena
        ).pack(anchor="w")

        entry_contrasena = ctk.CTkEntry(col_izq, show="*", width=260)
        entry_contrasena.pack(pady=(5,20))

        def modificar():

            global DF_MEDICAID, DF_AVILITY

            info = SEGUROS.get(seguro)
            if not info:
                messagebox.showerror("Error", "Seguro no reconocido.")
                return

            archivo = info["archivo"]

            if seguro == "medicaid":
                df = DF_MEDICAID.copy()
            else:
                df = DF_AVILITY.copy()

            idx = df["Usuario_App"].astype(str).str.strip() == usuario_app.strip()

            if not idx.any():
                messagebox.showerror("Error", "Usuario no encontrado.")
                return

            if cambiar_usuario.get():
                nuevo_usuario = entry_usuario.get().strip()
                if nuevo_usuario:
                    df.loc[idx, "Usuario"] = nuevo_usuario

            if cambiar_contrasena.get():
                nueva_contrasena = entry_contrasena.get().strip()
                if nueva_contrasena:
                    df.loc[idx, "contrasena"] = nueva_contrasena

            save_encrypted_excel(df, archivo, f)

            if seguro == "medicaid":
                DF_MEDICAID = df.copy()
            else:
                DF_AVILITY = df.copy()

            messagebox.showinfo("Éxito", "Credenciales actualizadas.")
            ventana.destroy()

        ctk.CTkButton(
            col_izq,
            text="Guardar cambios",
            command=modificar,
            width=260,
            height=40,
            fg_color="#f59e0b",
            hover_color="#d97706",
            text_color="black",
            font=("Segoe UI", 13, "bold")
        ).pack()

        # -------- IMAGEN DERECHA --------
        col_der = ctk.CTkFrame(frame, fg_color=BG_COLOR)
        col_der.pack(side="right", fill="both", expand=True)

        if os.path.exists(IMAGEN_FILE):

            imagen = Image.open(IMAGEN_FILE)

            imagen_ctk = ctk.CTkImage(
                light_image=imagen,
                dark_image=imagen,
                size=(260,260)
            )

            label_imagen = ctk.CTkLabel(
                col_der,
                image=imagen_ctk,
                text=""
            )
            label_imagen.pack(expand=True)
            label_imagen.image = imagen_ctk

    # ---------------- NO ----------------
    def no():
        confirm.destroy()

        if seguro == "medicaid":
            ventana_excels_medicaid(usuario_app)
        elif seguro == "avility":
            ventana_excels_avility(usuario_app)

    botones = ctk.CTkFrame(cont, fg_color=BG_COLOR)
    botones.pack(pady=(10,20))

    ctk.CTkButton(
        botones,
        text="Sí",
        width=120,
        fg_color="#16a34a",
        hover_color="#15803d",
        command=si
    ).pack(side="left", padx=15)

    ctk.CTkButton(
        botones,
        text="No",
        width=120,
        fg_color="#dc2626",
        hover_color="#b91c1c",
        command=no
    ).pack(side="right", padx=15)


def centrar_ventana(ventana, ancho=720, alto=360):

    def _centrar():

        ventana.update_idletasks()

        pantalla_ancho = ventana.winfo_screenwidth()
        pantalla_alto = ventana.winfo_screenheight()

        # ⭐ desplazamiento proporcional al monitor
        mover_derecha = int(pantalla_ancho * 0.16)

        x = int((pantalla_ancho - ancho) / 2) + mover_derecha
        y = int((pantalla_alto - alto) / 2)

        ventana.geometry(f"{ancho}x{alto}+{x}+{y}")

    ventana.after(120, _centrar)








def ventana_excels_medicaid(usuario):

    import customtkinter as ctk
    from tkinter import filedialog, messagebox
    import pandas as pd
    from PIL import Image
    import os

    BG_COLOR = "#f7f7f7"

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    IMAGEN_FILE = os.path.join(BASE_DIR, "Spectrum.jpg")

    excel_trabajadores = None
    excel_billing = None

    # -------- FUNCIONES --------
    def cargar_trabajadores():
        nonlocal excel_trabajadores
        ruta = filedialog.askopenfilename(
            title="Selecciona tu Excel de trabajadores",
            filetypes=[("Archivos Excel", "*.xlsx *.xls")]
        )
        if ruta:
            try:
                excel_trabajadores = pd.read_excel(ruta)
                messagebox.showinfo(
                    "Éxito",
                    f"Trabajadores cargados:\n{list(excel_trabajadores.columns)}"
                )
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo leer el archivo:\n{e}")

    def abrir_ejemplo_trabajadores():
        ruta = os.path.join(BASE_DIR, "BillingExport_2025-08-22T10_00_30_638914536306710260_451151.xlsx")

        if not os.path.exists(ruta):
            messagebox.showerror("Error", "No se encontró el archivo de ejemplo.")
            return

        try:
            if sys.platform == "win32":
                os.startfile(ruta)
            elif sys.platform == "darwin":
                subprocess.call(["open", ruta])
            else:
                subprocess.call(["xdg-open", ruta])
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el archivo:\n{e}")

    def cargar_billing():
        nonlocal excel_billing
        ruta = filedialog.askopenfilename(
            title="Selecciona tu Excel de billing",
            filetypes=[("Archivos Excel", "*.xlsx *.xls")]
        )
        if ruta:
            try:
                excel_billing = pd.read_excel(ruta, header=4, dtype={"Place of Service": str})
                messagebox.showinfo(
                    "Éxito",
                    f"Billing cargado:\n{list(excel_billing.columns)}"
                )
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo leer el archivo:\n{e}")

    def ejecutar_medicaid():
        if excel_trabajadores is None or excel_billing is None:
            messagebox.showerror("Error", "Debes cargar ambos archivos antes de ejecutar.")
            return

        medicaid_facturacion(excel_trabajadores, excel_billing, usuario)
        messagebox.showinfo("Proceso", "Facturación ejecutada con éxito.")

        ventana.destroy()
        escoger_seguro(usuario)

    # -------- VENTANA --------
    ventana = ctk.CTkToplevel()
    ventana.title("Facturación Medicaid")
    centrar_ventana(ventana, 720, 360)
    ventana.configure(fg_color=BG_COLOR)

    frame = ctk.CTkFrame(ventana, fg_color=BG_COLOR)
    frame.pack(fill="both", expand=True, padx=25, pady=20)

    # -------- IZQUIERDA --------
    col_izq = ctk.CTkFrame(frame, fg_color=BG_COLOR)
    col_izq.pack(side="left", fill="both", expand=True)

    ctk.CTkLabel(
        col_izq,
        text="Carga tus archivos Excel",
        font=("Segoe UI", 18, "bold"),
        text_color="black"
    ).pack(pady=(0,20))

    # Frame para alinear botón + ?
    frame_trabajadores = ctk.CTkFrame(col_izq, fg_color=BG_COLOR)
    frame_trabajadores.pack(pady=8)

    # Botón principal
    ctk.CTkButton(
        frame_trabajadores,
        text="Cargar Excel de Trabajadores",
        command=cargar_trabajadores,
        width=240,  # un poco más pequeño para que quepa el (?)
        height=42,
        fg_color="#2563eb",
        hover_color="#1d4ed8"
    ).pack(side="left", padx=(0, 6))

    # Botón de ayuda (?)
    ctk.CTkButton(
        frame_trabajadores,
        text="❓",
        width=40,
        height=42,
        fg_color="#e5e7eb",
        hover_color="#d1d5db",
        text_color="black",
        command=abrir_ejemplo_trabajadores
    ).pack(side="left")

    ctk.CTkButton(
        col_izq,
        text="Cargar Excel de Billing",
        command=cargar_billing,
        width=280,
        height=42,
        fg_color="#2563eb",
        hover_color="#1d4ed8"
    ).pack(pady=8)

    ctk.CTkButton(
        col_izq,
        text="Ejecutar Medicaid",
        command=ejecutar_medicaid,
        width=280,
        height=45,
        fg_color="#16a34a",
        hover_color="#15803d",
        font=("Segoe UI", 14, "bold")
    ).pack(pady=(20,0))

    # -------- DERECHA (IMAGEN) --------
    col_der = ctk.CTkFrame(frame, fg_color=BG_COLOR)
    col_der.pack(side="right", fill="both", expand=True)

    if os.path.exists(IMAGEN_FILE):

        imagen = Image.open(IMAGEN_FILE)

        imagen_ctk = ctk.CTkImage(
            light_image=imagen,
            dark_image=imagen,
            size=(260, 260)
        )

        label_imagen = ctk.CTkLabel(
            col_der,
            image=imagen_ctk,
            text=""
        )
        label_imagen.pack(expand=True)
        label_imagen.image = imagen_ctk



def ventana_excels_avility(usuario):

    import customtkinter as ctk
    from tkinter import filedialog, messagebox
    import pandas as pd
    from PIL import Image
    import os

    BG_COLOR = "#f7f7f7"

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    IMAGEN_FILE = os.path.join(BASE_DIR, "Spectrum.jpg")

    excel_billing = None

    def cargar_billing():
        nonlocal excel_billing

        ruta = filedialog.askopenfilename(
            title="Selecciona tu Excel de billing",
            filetypes=[("Archivos Excel", "*.xlsx *.xls")]
        )

        if ruta:
            try:
                excel_billing = pd.read_excel(
                    ruta,
                    header=4,
                    dtype={"Place of Service": str}
                )

                # guardar la ruta dentro del dataframe
                excel_billing.attrs["ruta_excel"] = ruta

                messagebox.showinfo("Éxito", "Billing cargado correctamente.")

            except Exception as e:
                messagebox.showerror("Error", f"No se pudo leer el archivo:\n{e}")
    def ejecutar_avilty():
        if excel_billing is None:
            messagebox.showerror("Error", "Debes cargar el archivo antes de ejecutar.")
            return

        silversumit_facturacion(excel_billing, usuario)
        messagebox.showinfo("Proceso", "Facturación ejecutada con éxito.")

        ventana.destroy()
        escoger_seguro(usuario)

    # -------- VENTANA --------
    ventana = ctk.CTkToplevel()
    ventana.title("Facturación Avility")
    centrar_ventana(ventana, 720, 360)
    ventana.configure(fg_color=BG_COLOR)

    frame = ctk.CTkFrame(ventana, fg_color=BG_COLOR)
    frame.pack(fill="both", expand=True, padx=25, pady=20)

    # -------- IZQUIERDA --------
    col_izq = ctk.CTkFrame(frame, fg_color=BG_COLOR)
    col_izq.pack(side="left", fill="both", expand=True)

    ctk.CTkLabel(
        col_izq,
        text="Carga tu archivo Excel",
        font=("Segoe UI", 18, "bold"),
        text_color="black"
    ).pack(pady=(0,20))

    ctk.CTkButton(
        col_izq,
        text="Cargar Excel de Billing",
        command=cargar_billing,
        width=280,
        height=42,
        fg_color="#2563eb",
        hover_color="#1d4ed8"
    ).pack(pady=8)

    ctk.CTkButton(
        col_izq,
        text="Ejecutar Avility",
        command=ejecutar_avilty,
        width=280,
        height=45,
        fg_color="#16a34a",
        hover_color="#15803d",
        font=("Segoe UI", 14, "bold")
    ).pack(pady=(20,0))

    # -------- DERECHA --------
    col_der = ctk.CTkFrame(frame, fg_color=BG_COLOR)
    col_der.pack(side="right", fill="both", expand=True)

    if os.path.exists(IMAGEN_FILE):

        imagen = Image.open(IMAGEN_FILE)

        imagen_ctk = ctk.CTkImage(
            light_image=imagen,
            dark_image=imagen,
            size=(260,260)
        )

        label_imagen = ctk.CTkLabel(col_der, image=imagen_ctk, text="")
        label_imagen.pack(expand=True)
        label_imagen.image = imagen_ctk

def iniciar_sesion():

    import customtkinter as ctk
    import tkinter as tk
    from tkinter import messagebox
    import os, io
    import pandas as pd
    from PIL import Image, ImageTk

    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")

    # 🎨 COLOR FONDO NUEVO
    BG_COLOR = "#f7f7f7"

    # ---------------- CARGAR USUARIOS ----------------

    def load_encrypted_excel(archivo, f):
        with open(archivo, "rb") as file:
            datos_encriptados = file.read()

        datos = f.decrypt(datos_encriptados)
        return pd.read_excel(io.BytesIO(datos))

    df = load_encrypted_excel(resource_path("medicaid-Usuarios.dat"), f)
    print(df)

    global DF_USUARIO_APP

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    ICONO_FILE = resource_path("Spectrum.ico")
    IMAGEN_FILE = resource_path("Spectrum.jpg")

    if DF_USUARIO_APP.empty:
        DF_USUARIO_APP = pd.DataFrame(columns=["Usuario", "contrasena"])

    # ---------------- FUNCIONES ----------------

    def verificar_usuario(usuario, contrasena):
        global DF_USUARIO_APP
        fila = DF_USUARIO_APP[
            (DF_USUARIO_APP["Usuario"] == usuario.strip()) &
            (DF_USUARIO_APP["contrasena"] == contrasena.strip())
        ]
        return not fila.empty

    def guardar_usuario(usuario, contrasena):
        global DF_USUARIO_APP

        usuario = usuario.strip()
        contrasena = contrasena.strip()

        if usuario == "" or contrasena == "":
            messagebox.showerror("Error", "No puedes dejar campos vacíos")
            return False

        if usuario in DF_USUARIO_APP["Usuario"].values:
            messagebox.showerror("Error", "Ese usuario ya existe.")
            return False

        nuevo = pd.DataFrame([[usuario, contrasena]],
                             columns=["Usuario", "contrasena"])

        DF_USUARIO_APP = pd.concat([DF_USUARIO_APP, nuevo], ignore_index=True)

        save_encrypted_excel(DF_USUARIO_APP, "usuarios_APP.dat", f)
        return True

    # ---------------- VENTANA ----------------

    login = ctk.CTk()
    login.title("Inicio de sesión")
    ICONO_FILE = resource_path("Spectrum.ico")


    if os.path.exists(ICONO_FILE):
        login.iconbitmap(ICONO_FILE)
    centrar_ventana(login, 820, 420)

    login.resizable(False, False)
    login.maxsize(820, 420)
    login.minsize(820, 420)

    # 🔥 FONDO APLICADO
    login.configure(fg_color=BG_COLOR)

    if os.path.exists(ICONO_FILE):
        login.iconbitmap(ICONO_FILE)

    frame = ctk.CTkFrame(login, fg_color=BG_COLOR, corner_radius=0)
    frame.pack(fill="both", expand=True)

    # -------- IZQUIERDA --------
    col_izq = ctk.CTkFrame(frame, fg_color=BG_COLOR)
    col_izq.pack(side="left", fill="both", expand=True, padx=50, pady=35)

    titulo = ctk.CTkLabel(
        col_izq,
        text="Inicio de Sesión",
        font=("Segoe UI", 22, "bold"),
        text_color="black"
    )
    titulo.pack(pady=(0,25))

    ctk.CTkLabel(col_izq, text="Usuario", text_color="black").pack(anchor="w")

    entry_usuario = ctk.CTkEntry(col_izq, width=320, height=34)
    entry_usuario.pack(pady=(5,20))

    # CONTRASEÑA
    ctk.CTkLabel(col_izq, text="Contraseña", text_color="black").pack(anchor="w")

    frame_pass = ctk.CTkFrame(col_izq, fg_color=BG_COLOR, width=320, height=34)
    frame_pass.pack()
    frame_pass.pack_propagate(False)

    entry_contrasena = ctk.CTkEntry(frame_pass, width=320, height=34, show="*")
    entry_contrasena.place(x=0, y=0)

    mostrar = False

    def toggle_password():
        nonlocal mostrar
        mostrar = not mostrar
        entry_contrasena.configure(show="" if mostrar else "*")
        btn_ojo.configure(text="🙈" if mostrar else "👁")

    btn_ojo = ctk.CTkButton(
        frame_pass,
        text="👁",
        width=30,
        height=26,
        fg_color="transparent",
        hover_color="#e5e7eb",
        text_color="black",
        command=toggle_password
    )
    btn_ojo.place(x=285, y=4)

    # -------- FUNCIONES BOTONES --------

    def iniciar():
        usuario = entry_usuario.get()
        contrasena = entry_contrasena.get()

        if verificar_usuario(usuario, contrasena):
            messagebox.showinfo("Éxito", f"Bienvenido {usuario}")
            login.withdraw()
            escoger_seguro(usuario)
        else:
            messagebox.showerror("Error", "Usuario o contraseña incorrectos.")

    def registrar():
        usuario = entry_usuario.get()
        contrasena = entry_contrasena.get()
        if guardar_usuario(usuario, contrasena):
            messagebox.showinfo("Éxito", "Cuenta creada correctamente.")

    ctk.CTkButton(
        col_izq,
        text="Iniciar sesión",
        command=iniciar,
        width=320,
        height=42,
        fg_color="#16a34a",
        hover_color="#15803d"
    ).pack(pady=(25,10))

    ctk.CTkButton(
        col_izq,
        text="Crear cuenta",
        command=registrar,
        width=320,
        height=42,
        fg_color="#2563eb",
        hover_color="#1d4ed8"
    ).pack()

    # -------- DERECHA --------
    col_der = ctk.CTkFrame(frame, fg_color=BG_COLOR)
    col_der.pack(side="right", fill="both", expand=True)

    if os.path.exists(IMAGEN_FILE):
        imagen = Image.open(IMAGEN_FILE)
        imagen = imagen.resize((460, 460))
        imagen_tk = ImageTk.PhotoImage(imagen)

        label_imagen = ctk.CTkLabel(
            col_der,
            image=imagen_tk,
            text="",
            fg_color=BG_COLOR
        )
        label_imagen.pack(expand=True)
        label_imagen.image = imagen_tk

    login.mainloop()
def escoger_seguro(usuario):

    import customtkinter as ctk
    from tkinter import messagebox
    import os
    from PIL import Image

    BG_COLOR = "#f7f7f7"

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    IMAGEN_FILE = os.path.join(BASE_DIR, "Spectrum.jpg")

    # -------- VENTANA --------
    ventana = ctk.CTkToplevel()
    ventana.title("Selección")
    centrar_ventana(ventana, 600, 600)

    ventana.resizable(False, False)
    ventana.maxsize(600, 600)
    ventana.minsize(600, 600)

    ventana.configure(fg_color=BG_COLOR)

    # -------- CONTENEDOR CENTRAL --------
    contenedor = ctk.CTkFrame(ventana, fg_color=BG_COLOR)
    contenedor.place(relx=0.5, rely=0.5, anchor="center")

    # -------- LOGO ARRIBA --------
    if os.path.exists(IMAGEN_FILE):

        imagen = Image.open(IMAGEN_FILE)

        imagen_ctk = ctk.CTkImage(
            light_image=imagen,
            dark_image=imagen,
            size=(300, 300)
        )

        label_imagen = ctk.CTkLabel(
            contenedor,
            image=imagen_ctk,
            text="",
            fg_color=BG_COLOR
        )

        label_imagen.pack(pady=(15,10))
        label_imagen.image = imagen_ctk

    # -------- LINEA SEPARADORA --------
    divider = ctk.CTkFrame(
        contenedor,
        width=320,
        height=2,
        fg_color="#e5e7eb"
    )
    divider.pack(pady=(5,20))

    # -------- TITULO --------
    titulo = ctk.CTkLabel(
        contenedor,
        text="Selecciona la plataforma",
        font=("Segoe UI", 20, "bold"),
        text_color="black"
    )
    titulo.pack(pady=(0,25))

    # -------- FUNCIONES --------
    def elegir_medicaid():
        messagebox.showinfo("", "Has elegido Medicaid")
        ventana.destroy()
        ventana_medicaid(usuario)

    def elegir_avilty():
        messagebox.showinfo("", "Has elegido Avilty")
        ventana.destroy()
        ventana_avilty(usuario)

    # -------- BOTONES --------
    ctk.CTkButton(
        contenedor,
        text="Medicaid",
        command=elegir_medicaid,
        width=320,
        height=45,
        fg_color="#16a34a",
        hover_color="#15803d",
        font=("Segoe UI", 14, "bold")
    ).pack(pady=(0,15))

    ctk.CTkButton(
        contenedor,
        text="Avilty",
        command=elegir_avilty,
        width=320,
        height=45,
        fg_color="#2563eb",
        hover_color="#1d4ed8",
        font=("Segoe UI", 14, "bold")
    ).pack()


def ventana_avilty(usuario_app):

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    ICONO_FILE = resource_path("Spectrum.ico")
    IMAGEN_FILE = resource_path("Spectrum.jpg")
    ventana = tk.Tk()
    ventana.title("Credenciales Avilty")
    centrar_ventana(ventana, 700, 520)



    # Icono
    if os.path.exists(ICONO_FILE):
        ventana.iconbitmap(ICONO_FILE)

    frame = tk.Frame(ventana)
    frame.pack(fill="both", expand=True)

    # Columna izquierda (formulario)
    col_izq = tk.Frame(frame)
    col_izq.pack(side="left", fill="both", expand=True, padx=20, pady=20)

    tk.Label(col_izq, text="Gestión de credenciales Avility", font=("Arial", 14, "bold")).pack(pady=10)

    # Leer archivo para ver si ya existe usuario Medicaid
    df = DF_AVILITY.copy()
    fila = df[df["Usuario_App"] == usuario_app]

    if fila.empty:

        # Primera vez → pedir usuario y contraseña
        tk.Label(col_izq, text="Usuario").pack(pady=5)
        entry_usuario = tk.Entry(col_izq)
        entry_usuario.pack(pady=5)

        tk.Label(col_izq, text="Contraseña").pack(pady=5)
        entry_contrasena = tk.Entry(col_izq, show="*")
        entry_contrasena.pack(pady=5)

        # Función para alternar visibilidad
        def toggle_password():
            if entry_contrasena.cget("show") == "":
                entry_contrasena.config(show="*")
            else:
                entry_contrasena.config(show="")

        # Checkbox para mos trar/ocultar
        ver_contrasena = tk.Checkbutton(col_izq, text="Ver contraseña", command=toggle_password)
        ver_contrasena.pack(pady=5)

        messagebox.showinfo("Info", "Por ser tu primera vez por favor guarda tu usuario y contraseña de Avility.")

        def guardar():
            usuario_avility= entry_usuario.get()
            contrasena_avility= entry_contrasena.get()

            if not usuario_avility or not contrasena_avility:
                messagebox.showerror("Error", "Debes llenar ambos campos.")
                return

            seguro = messagebox.askyesno("Confirmar", f"¿Seguro que quieres guardar el usuario {usuario_avility}?")
            if seguro:
                # Leer archivo
                df = DF_USUARIO_APP.copy()

                # Crear nuevo registro con la columna extra Usuario_App
                nuevo = pd.DataFrame(
                    [[usuario_avility, contrasena_avility, usuario_app]],
                    columns=["Usuario", "contrasena", "Usuario_App"]
                )

                # Agregar al DataFrame
                df = pd.concat([df, nuevo], ignore_index=True)

                # Guardar
                save_encrypted_excel(
                    df,
                    "avility-Usuarios.dat",
                    f
                )

                messagebox.showinfo("Éxito", "Credenciales guardadas correctamente.")
                ventana.destroy()
        tk.Button(col_izq, text="Guardar", bg="green", fg="white", command=guardar).pack(pady=10)

    else:
            ventana.destroy()
            preguntar_modificar(usuario_app,"avility")




def ventana_medicaid(usuario_app):

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    ICONO_FILE = resource_path("Spectrum.ico")
    IMAGEN_FILE = resource_path("Spectrum.jpg")
    ventana = tk.Tk()
    ventana.title("Credenciales Medicaid")
    centrar_ventana(ventana,700)



    # Icono
    if os.path.exists(ICONO_FILE):
        ventana.iconbitmap(ICONO_FILE)

    frame = tk.Frame(ventana)
    frame.pack(fill="both", expand=True)

    # Columna izquierda (formulario)
    col_izq = tk.Frame(frame)
    col_izq.pack(side="left", fill="both", expand=True, padx=20, pady=20)

    tk.Label(col_izq, text="Gestión de credenciales Medicaid", font=("Arial", 14, "bold")).pack(pady=10)

    # Leer archivo para ver si ya existe usuario Medicaid
    df = DF_MEDICAID.copy()
    fila = df[df["Usuario_App"] == usuario_app]

    if fila.empty:

        # Primera vez → pedir usuario y contraseña
        tk.Label(col_izq, text="Usuario Medicaid").pack(pady=5)
        entry_usuario = tk.Entry(col_izq)
        entry_usuario.pack(pady=5)

        tk.Label(col_izq, text="Contraseña Medicaid").pack(pady=5)
        entry_contrasena = tk.Entry(col_izq, show="*")
        entry_contrasena.pack(pady=5)

        # Función para alternar visibilidad
        def toggle_password():
            if entry_contrasena.cget("show") == "":
                entry_contrasena.config(show="*")
            else:
                entry_contrasena.config(show="")

        # Checkbox para mostrar/ocultar
        ver_contrasena = tk.Checkbutton(col_izq, text="Ver contraseña", command=toggle_password)
        ver_contrasena.pack(pady=5)

        messagebox.showinfo("Info", "Por ser tu primera vez por favor guarda tu usuario y contraseña de Medicaid.")

        def guardar():
            usuario_medicaid = entry_usuario.get()
            contrasena_medicaid = entry_contrasena.get()

            if not usuario_medicaid or not contrasena_medicaid:
                messagebox.showerror("Error", "Debes llenar ambos campos.")
                return

            seguro = messagebox.askyesno("Confirmar", f"¿Seguro que quieres guardar el usuario {usuario_medicaid}?")
            if seguro:
                # Leer archivo
                df = DF_USUARIO_APP.copy()

                # Crear nuevo registro con la columna extra Usuario_App
                nuevo = pd.DataFrame(
                    [[usuario_medicaid, contrasena_medicaid, usuario_app]],
                    columns=["Usuario", "contrasena", "Usuario_App"]
                )

                # Agregar al DataFrame
                df = pd.concat([df, nuevo], ignore_index=True)

                # Guardar
                save_encrypted_excel(
                    df,
                    "medicaid-Usuarios.dat",
                    f
                )

                messagebox.showinfo("Éxito", "Credenciales guardadas correctamente.")
                ventana.destroy()

        tk.Button(col_izq, text="Guardar", bg="green", fg="white", command=guardar).pack(pady=10)

    else:
            ventana.destroy()
            preguntar_modificar(usuario_app,"medicaid")

