import os
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import time
from Avility.molina import molina_facturacion
from Avility.silversumit import silversumit_facturacion
from Medicaid.medicaid import medicaid_facturacion
from PIL import Image, ImageTk  # si tu imagen es JPG/PNG
from cryptography.fernet import Fernet
import io


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

DF_AVILITY = load_encrypted_excel("avility-Usuarios.dat")
DF_MEDICAID = load_encrypted_excel("medicaid-Usuarios.dat")
DF_USUARIO_APP = load_encrypted_excel("usuarios_APP.dat")

def preguntar_modificar(usuario_app, seguro):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    ICONO_FILE = os.path.join(BASE_DIR, "Spectrum.ico")
    IMAGEN_FILE = os.path.join(BASE_DIR, "Spectrum.jpg")



    confirm = tk.Tk()
    confirm.title("Confirmación")
    centrar_ventana(confirm, 300, 150)

    tk.Label(confirm, text=f"¿Quieres modificar tu contraseña de {seguro}?", font=("Arial", 10)).pack(pady=20)

    def si():
        ventana = tk.Tk()
        ventana.title(f"Credenciales {seguro}")
        centrar_ventana(ventana, 700)

        if os.path.exists(ICONO_FILE):
            ventana.iconbitmap(ICONO_FILE)

        frame = tk.Frame(ventana)
        frame.pack(fill="both", expand=True)

        col_izq = tk.Frame(frame)
        col_izq.pack(side="left", fill="both", expand=True, padx=20, pady=20)

        tk.Label(col_izq, text=f"Gestión de credenciales {seguro}", font=("Arial", 14, "bold")).pack(pady=10)

        df = DF_USUARIO_APP.copy()
        fila = df[df["Usuario_App"] == usuario_app]

        # ✅ cerrar solo la ventana de confirmación (que debe ser Toplevel)
        confirm.destroy()

        tk.Label(col_izq, text=f"Usuario {seguro}: {usuario_app}", font=("Arial", 12)).pack(pady=10)
        tk.Label(col_izq, text="Nueva contraseña").pack(pady=5)
        entry_contrasena = tk.Entry(col_izq, show="*")
        entry_contrasena.pack(pady=5)

        def modificar():
            # Cargar SIEMPRE el archivo original
            df = DF_USUARIO_APP.copy()

            nueva_contrasena = entry_contrasena.get()
            print(nueva_contrasena)
            print(usuario_app)

            if not nueva_contrasena:
                messagebox.showerror("Error", "Debes ingresar una nueva contraseña.")
                return

            # Normalizar para evitar espacios invisibles
            df["Usuario_App"] = df["Usuario_App"].astype(str).str.strip()
            usuario_normalizado = usuario_app.strip()

            # Modificar la contraseña
            df.loc[df["Usuario_App"] == usuario_normalizado, "contrasena"] = nueva_contrasena

            print(df.loc[df["Usuario_App"] == usuario_normalizado, "contrasena"])

            # Guardar en el archivo original
            save_encrypted_excel(
                df,
                "usuarios_APP.dat",
                f
            )

            messagebox.showinfo("Éxito", "Credenciales guardadas correctamente.")
            ventana.destroy()

        tk.Button(col_izq, text="Modificar contraseña", bg="orange", fg="black", command=modificar).pack(pady=10)

        col_der = tk.Frame(frame)
        col_der.pack(side="right", fill="both", expand=True, padx=20, pady=20)

        if os.path.exists(IMAGEN_FILE):
            imagen = Image.open(IMAGEN_FILE)
            imagen = imagen.resize((250, 250))
            imagen_tk = ImageTk.PhotoImage(imagen, master=ventana)
            label_imagen = tk.Label(col_der, image=imagen_tk)
            label_imagen.pack()
            label_imagen.image = imagen_tk

    def no():
        confirm.destroy()
        if seguro=="medicaid":
            ventana_excels_medicaid(usuario_app)
        if seguro=="avility":
            escoger_seguro_avilty(usuario_app)


    tk.Button(confirm, text="Sí", width=10, bg="green", fg="white", command=si).pack(side="left", padx=30, pady=20)
    tk.Button(confirm, text="No", width=10, bg="red", fg="white", command=no).pack(side="right", padx=30, pady=20)








def centrar_ventana(ventana, ancho=600, alto=300):
    ventana.update_idletasks()
    pantalla_ancho = ventana.winfo_screenwidth()
    pantalla_alto = ventana.winfo_screenheight()
    x = (pantalla_ancho // 2) - (ancho // 2)
    y = (pantalla_alto // 2) - (alto // 2)
    ventana.geometry(f"{ancho}x{alto}+{x}+{y}")






def ventana_excels_medicaid(usuario):
    excel_trabajadores = None
    excel_billing = None

    def cargar_trabajadores():
        nonlocal excel_trabajadores
        ruta = filedialog.askopenfilename(
            title="Selecciona tu Excel de trabajadores",
            filetypes=[("Archivos Excel", "*.xlsx *.xls")]
        )
        if ruta:
            try:
                excel_trabajadores = pd.read_excel(ruta)
                messagebox.showinfo("Éxito", f"Trabajadores cargados: {ruta}\nColumnas: {list(excel_trabajadores.columns)}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo leer el archivo:\n{e}")

    def cargar_billing():
        nonlocal excel_billing
        ruta = filedialog.askopenfilename(
            title="Selecciona tu Excel de billing",
            filetypes=[("Archivos Excel", "*.xlsx *.xls")]
        )
        if ruta:
            try:
                excel_billing = pd.read_excel(ruta, header=4, dtype={"Place of Service": str})
                messagebox.showinfo("Éxito", f"Billing cargado: {ruta}\nColumnas: {list(excel_billing.columns)}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo leer el archivo:\n{e}")

    def ejecutar_medicaid():
        if excel_trabajadores is None or excel_billing is None:
            messagebox.showerror("Error", "Debes cargar ambos archivos antes de ejecutar.")
            return
        medicaid_facturacion(excel_trabajadores, excel_billing,usuario)
        messagebox.showinfo("Proceso", "Facturación ejecutada con éxito.")
        ventana.destroy()
        escoger_seguro(usuario)

    ventana = tk.Tk()
    ventana.title("Facturación Seguros")
    centrar_ventana(ventana,600,300)

    # Crear un frame con dos columnas
    frame = tk.Frame(ventana)
    frame.pack(fill="both", expand=True)

    # Columna izquierda (texto y botones)
    col_izq = tk.Frame(frame)
    col_izq.pack(side="left", fill="both", expand=True, padx=20, pady=20)

    tk.Label(col_izq, text="Carga tus archivos Excel", font=("Arial", 12)).pack(pady=10)
    tk.Button(col_izq, text="Cargar Excel de Trabajadores", command=cargar_trabajadores, width=25, height=2).pack(pady=5)
    tk.Button(col_izq, text="Cargar Excel de Billing", command=cargar_billing, width=25, height=2).pack(pady=5)
    tk.Button(col_izq, text="Ejecutar Medicaid", command=ejecutar_medicaid, width=25, height=2, bg="green", fg="white").pack(pady=20)

    # Columna derecha (imagen)
    col_der = tk.Frame(frame)
    col_der.pack(side="right", fill="both", expand=True, padx=20, pady=20)



    # ✅ Cargar imagen dentro de esta ventana
    imagen = Image.open("Spectrum.jpg")
    imagen = imagen.resize((330, 330))
    imagen_tk = ImageTk.PhotoImage(imagen)
    ventana.iconbitmap("Spectrum.ico")

    label_imagen = tk.Label(col_der, image=imagen_tk)
    label_imagen.image = imagen_tk  # mantener referencia
    label_imagen.pack()

def ventana_excels_molina(usuario):
    excel_billing = None
    def cargar_billing():
        nonlocal excel_billing
        ruta = filedialog.askopenfilename(
            title="Selecciona tu Excel de billing",
            filetypes=[("Archivos Excel", "*.xlsx *.xls")]
        )
        if ruta:
            try:
                excel_billing = pd.read_excel(ruta, header=4, dtype={"Place of Service": str})
                messagebox.showinfo("Éxito", f"Billing cargado: {ruta}\nColumnas: {list(excel_billing.columns)}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo leer el archivo:\n{e}")

    def ejecutar_avilty():
        if  excel_billing is None:
            messagebox.showerror("Error", "Debes cargar el archivo antes de ejecutar.")
            return
        molina_facturacion(excel_billing,usuario)
        messagebox.showinfo("Proceso", "Facturación ejecutada con éxito.")
        ventana.destroy()
        escoger_seguro(usuario)

    ventana = tk.Tk()
    ventana.title("Facturación Seguros")
    centrar_ventana(ventana,600,300)

    # Crear un frame con dos columnas
    frame = tk.Frame(ventana)
    frame.pack(fill="both", expand=True)

    # Columna izquierda (texto y botones)
    col_izq = tk.Frame(frame)
    col_izq.pack(side="left", fill="both", expand=True, padx=20, pady=20)

    tk.Label(col_izq, text="Carga tus archivos Excel", font=("Arial", 12)).pack(pady=10)
    tk.Button(col_izq, text="Cargar Excel de Billing", command=cargar_billing, width=25, height=2).pack(pady=5)
    tk.Button(col_izq, text="Ejecutar Avility", command=ejecutar_avilty, width=25, height=2, bg="green", fg="white").pack(pady=20)

    # Columna derecha (imagen)
    col_der = tk.Frame(frame)
    col_der.pack(side="right", fill="both", expand=True, padx=20, pady=20)



    # ✅ Cargar imagen dentro de esta ventana
    imagen = Image.open("Spectrum.jpg")
    imagen = imagen.resize((330, 330))
    imagen_tk = ImageTk.PhotoImage(imagen)
    ventana.iconbitmap("Spectrum.ico")

    label_imagen = tk.Label(col_der, image=imagen_tk)
    label_imagen.image = imagen_tk  # mantener referencia
    label_imagen.pack()

def ventana_excels_silversumit(usuario):
    excel_billing = None
    def cargar_billing():
        nonlocal excel_billing
        ruta = filedialog.askopenfilename(
            title="Selecciona tu Excel de billing",
            filetypes=[("Archivos Excel", "*.xlsx *.xls")]
        )
        if ruta:
            try:
                excel_billing = pd.read_excel(ruta, header=4, dtype={"Place of Service": str})
                messagebox.showinfo("Éxito", f"Billing cargado: {ruta}\nColumnas: {list(excel_billing.columns)}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo leer el archivo:\n{e}")

    def ejecutar_avilty():
        if  excel_billing is None:
            messagebox.showerror("Error", "Debes cargar el archivo antes de ejecutar.")
            return
        silversumit_facturacion(excel_billing,usuario)
        messagebox.showinfo("Proceso", "Facturación ejecutada con éxito.")
        ventana.destroy()
        escoger_seguro(usuario)

    ventana = tk.Tk()
    ventana.title("Facturación Seguros")
    centrar_ventana(ventana,600,300)

    # Crear un frame con dos columnas
    frame = tk.Frame(ventana)
    frame.pack(fill="both", expand=True)

    # Columna izquierda (texto y botones)
    col_izq = tk.Frame(frame)
    col_izq.pack(side="left", fill="both", expand=True, padx=20, pady=20)

    tk.Label(col_izq, text="Carga tus archivos Excel", font=("Arial", 12)).pack(pady=10)
    tk.Button(col_izq, text="Cargar Excel de Billing", command=cargar_billing, width=25, height=2).pack(pady=5)
    tk.Button(col_izq, text="Ejecutar Avility", command=ejecutar_avilty, width=25, height=2, bg="green", fg="white").pack(pady=20)

    # Columna derecha (imagen)
    col_der = tk.Frame(frame)
    col_der.pack(side="right", fill="both", expand=True, padx=20, pady=20)



    # ✅ Cargar imagen dentro de esta ventana
    imagen = Image.open("Spectrum.jpg")
    imagen = imagen.resize((330, 330))
    imagen_tk = ImageTk.PhotoImage(imagen)
    ventana.iconbitmap("Spectrum.ico")

    label_imagen = tk.Label(col_der, image=imagen_tk)
    label_imagen.image = imagen_tk  # mantener referencia
    label_imagen.pack()


def iniciar_sesion():
    global DF_USUARIO_APP
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    ICONO_FILE = os.path.join(BASE_DIR, "Spectrum.ico")  # icono .ico
    IMAGEN_FILE = os.path.join(BASE_DIR, "Spectrum.jpg")  # imagen derecha

    # Crear archivo de usuarios si no existe
    if DF_USUARIO_APP.empty:
        DF_USUARIO_APP = pd.DataFrame(columns=["Usuario", "contrasena"])

    def verificar_usuario(usuario, contrasena):
        global DF_USUARIO_APP

        usuario = usuario.strip()
        contrasena = contrasena.strip()

        fila = DF_USUARIO_APP[
            (DF_USUARIO_APP["Usuario"] == usuario) &
            (DF_USUARIO_APP["contrasena"] == contrasena)
            ]
        return not fila.empty

    def guardar_usuario(usuario, contrasena):
        global DF_USUARIO_APP

        usuario = usuario.strip()
        contrasena = contrasena.strip()

        if usuario == "" or contrasena == "":
            messagebox.showerror(
                "Error", "No puedes crear un usuario o contraseña en blanco"
            )
            return False

        if usuario in DF_USUARIO_APP["Usuario"].values:
            messagebox.showerror("Error", "Ese usuario ya existe.")
            return False

        nuevo = pd.DataFrame(
            [[usuario, contrasena]],
            columns=["Usuario", "contrasena"]
        )

        # 🔁 ACTUALIZAR MEMORIA
        DF_USUARIO_APP = pd.concat(
            [DF_USUARIO_APP, nuevo],
            ignore_index=True
        )

        # 🔐 GUARDAR CIFRADO
        save_encrypted_excel(
            DF_USUARIO_APP,
            "usuarios_APP.dat",
            f
        )

        return True

    login = tk.Tk()
    login.title("Inicio de sesión")
    centrar_ventana(login,600,300)
    # Icono de la ventana
    if os.path.exists(ICONO_FILE):
        login.iconbitmap(ICONO_FILE)

    # Frame principal con dos columnas
    frame = tk.Frame(login)
    frame.pack(fill="both", expand=True)

    # Columna izquierda (usuario/contraseña)
    col_izq = tk.Frame(frame)
    col_izq.pack(side="left", fill="both", expand=True, padx=20, pady=20)

    tk.Label(col_izq, text="Usuario").pack(pady=5)
    entry_usuario = tk.Entry(col_izq)
    entry_usuario.pack(pady=5)

    tk.Label(col_izq, text="Contraseña").pack(pady=5)
    entry_contrasena = tk.Entry(col_izq, show="*")
    entry_contrasena.pack(pady=5)


    def iniciar():
        usuario = entry_usuario.get()
        contrasena = entry_contrasena.get()
        if verificar_usuario(usuario, contrasena):
            messagebox.showinfo("Éxito", f"Bienvenido {usuario}")
            login.destroy()
            escoger_seguro(usuario)
            # Aquí llamas tu ventana principal

        else:
            messagebox.showerror("Error", "Usuario o contraseña incorrectos.")

    def registrar():
        usuario = entry_usuario.get()
        contrasena = entry_contrasena.get()
        if guardar_usuario(usuario, contrasena):
            messagebox.showinfo("Éxito", "Cuenta creada correctamente.")

    tk.Button(col_izq, text="Iniciar sesión", command=iniciar,width=25, height=2, bg="green", fg="white").pack(pady=10)
    tk.Button(col_izq, text="Crear cuenta", command=registrar,width=25, height=2, bg="blue", fg="white").pack(pady=5)

    # Columna derecha (imagen/logo)
    col_der = tk.Frame(frame)
    col_der.pack(side="right", fill="both", expand=True, padx=20, pady=20)

    if os.path.exists(IMAGEN_FILE):
        imagen = Image.open(IMAGEN_FILE)
        imagen = imagen.resize((250, 250))
        imagen_tk = ImageTk.PhotoImage(imagen)
        label_imagen = tk.Label(col_der, image=imagen_tk)
        label_imagen.pack()
        label_imagen.image = imagen_tk  # mantener referencia

    login.mainloop()

def escoger_seguro(usuario):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    ICONO_FILE = os.path.join(BASE_DIR, "Spectrum.ico")  # icono .ico
    IMAGEN_FILE = os.path.join(BASE_DIR, "Spectrum.jpg")  # imagen derecha


    ventana = tk.Tk()
    ventana.title("Seleccion")
    centrar_ventana(ventana)

    # Icono de la ventana
    if os.path.exists(ICONO_FILE):
        ventana.iconbitmap(ICONO_FILE)

    # Frame principal con dos columnas
    frame = tk.Frame(ventana)
    frame.pack(fill="both", expand=True)

    # Columna izquierda (opciones de seguro)
    col_izq = tk.Frame(frame)
    col_izq.pack(side="left", fill="both", expand=True, padx=20, pady=20)

    tk.Label(col_izq, text="Selecciona tu forma de Facturar", font=("Arial", 14)).pack(pady=10)

    def elegir_medicaid():
        tk.messagebox.showinfo("", "Has elegido Medicaid")
        ventana.destroy()
        ventana_medicaid(usuario)
        # aquí puedes llamar a tu función medicaid_facturacion()

    def elegir_avilty():
        tk.messagebox.showinfo("", "Has elegido Avilty")
        ventana.destroy()
        ventana_avilty(usuario)



    tk.Button(col_izq, text="Medicaid", width=20, height=2, bg="green", fg="white",  font=("Arial", 10, "bold"),  command=elegir_medicaid).pack(
        pady=10)
    tk.Button(col_izq, text="Avilty", width=20, height=2, bg="blue", fg="white",font=("Arial", 10, "bold"), command=elegir_avilty).pack(
        pady=10)

    # Columna derecha (imagen/logo)
    col_der = tk.Frame(frame)
    col_der.pack(side="right", fill="both", expand=True, padx=20, pady=20)

    if os.path.exists(IMAGEN_FILE):
        imagen = Image.open(IMAGEN_FILE)
        imagen = imagen.resize((250, 250))
        imagen_tk = ImageTk.PhotoImage(imagen)
        label_imagen = tk.Label(col_der, image=imagen_tk)
        label_imagen.pack()
        label_imagen.image = imagen_tk  # mantener referencia

    ventana.mainloop()

def escoger_seguro_avilty(usuario):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    ICONO_FILE = os.path.join(BASE_DIR, "Spectrum.ico")  # icono .ico
    IMAGEN_FILE = os.path.join(BASE_DIR, "Spectrum.jpg")  # imagen derecha


    ventana = tk.Tk()
    ventana.title("Seleccion")
    centrar_ventana(ventana)

    # Icono de la ventana
    if os.path.exists(ICONO_FILE):
        ventana.iconbitmap(ICONO_FILE)

    # Frame principal con dos columnas
    frame = tk.Frame(ventana)
    frame.pack(fill="both", expand=True)

    # Columna izquierda (opciones de seguro)
    col_izq = tk.Frame(frame)
    col_izq.pack(side="left", fill="both", expand=True, padx=20, pady=20)

    tk.Label(col_izq, text="Selecciona el Seguro", font=("Arial", 14)).pack(pady=10)

    def elegir_silversumit():
        tk.messagebox.showinfo("", "Has elegido Silversumit")
        ventana.destroy()
        ventana_excels_silversumit(usuario)


        # aquí puedes llamar a tu función medicaid_facturacion()

    def elegir_molina():
        tk.messagebox.showinfo("", "Has elegido Molina")
        ventana.destroy()
        ventana_excels_molina(usuario)

    tk.Button(col_izq, text="Silversummit", width=20, height=2, bg="green", fg="white",  font=("Arial", 10, "bold"),  command=elegir_silversumit).pack(
        pady=10)
    tk.Button(col_izq, text="Molina", width=20, height=2, bg="blue", fg="white",font=("Arial", 10, "bold"), command=elegir_molina).pack(
        pady=10)

    # Columna derecha (imagen/logo)
    col_der = tk.Frame(frame)
    col_der.pack(side="right", fill="both", expand=True, padx=20, pady=20)

    if os.path.exists(IMAGEN_FILE):
        imagen = Image.open(IMAGEN_FILE)
        imagen = imagen.resize((250, 250))
        imagen_tk = ImageTk.PhotoImage(imagen)
        label_imagen = tk.Label(col_der, image=imagen_tk)
        label_imagen.pack()
        label_imagen.image = imagen_tk  # mantener referencia

    ventana.mainloop()


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICONO_FILE = os.path.join(BASE_DIR, "Spectrum.ico")
IMAGEN_FILE = os.path.join(BASE_DIR, "Spectrum.jpg")


# Crear archivo si no existe
if DF_USUARIO_APP.empty:
    DF_USUARIO_APP = pd.DataFrame(columns=["Usuario", "contrasena"])


def ventana_avilty(usuario_app):

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    ICONO_FILE = os.path.join(BASE_DIR, "Spectrum.ico")
    IMAGEN_FILE = os.path.join(BASE_DIR, "Spectrum.jpg")
    ventana = tk.Tk()
    ventana.title("Credenciales Avilty")
    centrar_ventana(ventana,700)



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

        # Checkbox para mostrar/ocultar
        ver_contrasena = tk.Checkbutton(col_izq, text="Ver contraseña", command=toggle_password)
        ver_contrasena.pack(pady=5)

        messagebox.showinfo("Info", "Por ser tu primera vez por favor guarda tu usuario y contraseña de Avility.")

        def guardar():
            usuario_avilty = entry_usuario.get()
            contrasena_avilty = entry_contrasena.get()

            if not usuario_avilty or not  contrasena_avilty:
                messagebox.showerror("Error", "Debes llenar ambos campos.")
                return

            seguro = messagebox.askyesno("Confirmar", f"¿Seguro que quieres guardar el usuario {usuario_avilty}?")
            if seguro:
                # Leer archivo
                df = DF_USUARIO_APP.copy()

                # Crear nuevo registro con la columna extra Usuario_App
                nuevo = pd.DataFrame(
                    [[usuario_avilty, contrasena_avilty, usuario_app]],
                    columns=["Usuario", "contrasena", "Usuario_App"]
                )

                # Agregar al DataFrame
                df = pd.concat([df, nuevo], ignore_index=True)

                # Guardar
                save_encrypted_excel(
                    df,
                    "usuarios_APP.dat",
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
    ICONO_FILE = os.path.join(BASE_DIR, "Spectrum.ico")
    IMAGEN_FILE = os.path.join(BASE_DIR, "Spectrum.jpg")
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
                    "usuarios_APP.dat",
                    f
                )

                messagebox.showinfo("Éxito", "Credenciales guardadas correctamente.")
                ventana.destroy()

        tk.Button(col_izq, text="Guardar", bg="green", fg="white", command=guardar).pack(pady=10)

    else:
            ventana.destroy()
            preguntar_modificar(usuario_app,"medicaid")

