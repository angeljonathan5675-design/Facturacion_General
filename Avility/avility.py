from time import sleep
from tkinter import Tk, filedialog
from tkinter import messagebox
import tkinter as tk
from cryptography.fernet import Fernet
from selenium import webdriver
from selenium.common import TimeoutException, ElementClickInterceptedException, StaleElementReferenceException
from selenium.webdriver.common.by import By
#from selenium.webdriver.common.devtools.v141.performance_timeline import LayoutShift
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select
import pandas as pd
import time
import json
import io
import sys
import os

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

PROGRESO_FILE = "progreso_facturacion.json"
KEY = b'HzzXD8zy3oXBb-kNV_S-ElF0631LsAMzWdHh1wZOiLw='
f = Fernet(KEY)
def load_encrypted_excel(path):
    with open(path, "rb") as file:
        encrypted_data = file.read()

    decrypted_data = f.decrypt(encrypted_data)
    df = pd.read_excel(io.BytesIO(decrypted_data))

    nombre_archivo = os.path.basename(path)  # nombre del archivo
    return df, nombre_archivo

DF_AVILITY, nombre_excel = load_encrypted_excel(resource_path("avility-Usuarios.dat"))

def   silversumit_facturacion(excel_billing,usuario_app):
    ruta_excel = excel_billing.attrs.get("ruta_excel")
    archivo_actual = os.path.basename(ruta_excel)

    ruta_excel = excel_billing.attrs.get("ruta_excel")

    if not ruta_excel:
        raise ValueError("No se encontró la ruta del Excel.")

    archivo_actual = os.path.basename(ruta_excel)

    from tkinter import messagebox
    import tkinter as tk

    def preguntar_archivo(archivo_guardado, archivo_actual):
        root = tk._default_root

        if root:
            # traer ventana al frente
            root.lift()
            root.attributes('-topmost', True)
            root.update()

        respuesta = messagebox.askyesno(
            "Progreso detectado",
            f"Archivo anterior: {archivo_guardado}\n"
            f"Archivo actual: {archivo_actual}\n\n"
            "¿Desea borrar el progreso y continuar?"
        )

        if root:
            # devolver a estado normal
            root.attributes('-topmost', False)

        return respuesta

    def mostrar_alerta(driver, mensaje):
        driver.execute_script("alert(arguments[0]);", mensaje)


    def guardar_progreso(client_index, provider_index, ciclo,nombre_excel):
        data = {
            "client_index": client_index,
            "provider_index": provider_index,
            "ciclo": ciclo,
            "nombre_billing": nombre_excel

        }
        with open(PROGRESO_FILE, "w") as f:
            json.dump(data, f)

    def cargar_progreso():
        if os.path.exists(PROGRESO_FILE):
            with open(PROGRESO_FILE, "r") as f:
                return json.load(f)
        return None

    def limpiar_progreso():
        if os.path.exists(PROGRESO_FILE):
            os.remove(PROGRESO_FILE)

    def autocompletar(valor, texto, campo):
        if campo == "formulario":
            select_provider = driver.find_element(By.XPATH, value=valor)
        else:
            select_provider = driver.find_element(By.NAME, value=valor)

        # 🔥 Limpiar el campo SI tiene algo
        if select_provider.get_attribute("value"):
            select_provider.send_keys(Keys.CONTROL + "a")
            select_provider.send_keys(Keys.DELETE)

        # Escribir nuevo texto
        select_provider.send_keys(texto)

        time.sleep(1)

        first_option = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "li.MuiAutocomplete-option"))
        )
        first_option.click()

    excel= excel_billing
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option("detach", True)

    driver = webdriver.Chrome(options=chrome_options)
    driver.get("https://essentials.availity.com/static/public/onb/onboarding-ui-apps/availity-fr-ui/#/login")
    print(excel["Client Name"].unique())
    total_clientes=excel["Client Name"].nunique()
    print(total_clientes)

    # Agrupar por cliente y contar proveedores distintos
    conteo_por_cliente = excel.groupby("Client Name")["Provider Name"].nunique().reset_index(name="Num_Providers")
    # Calcular el total de proveedores distintos sumando todos
    total_providers = conteo_por_cliente["Num_Providers"].sum()
    # ------------------------------------------------------------------------------------------------

    print(total_providers)
    #-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # =========================
    # CLIENTES - MAX 8 HORAS
    # =========================
    cliente_dia = (
        excel
        .groupby(["Client Name", "Date of Service"])["# of Hours"]
        .sum()
        .reset_index()
    )

    clientes_excedidos = cliente_dia[cliente_dia["# of Hours"] > 8]

    if not clientes_excedidos.empty:
        fila = clientes_excedidos.iloc[0]

        mensaje = (
            f"ERROR DE HORAS (CLIENTE)\n\n"
            f"Cliente: {fila['Client Name']}\n"
            f"Fecha: {fila['Date of Service'].strftime('%m/%d/%Y')}\n"
            f"Horas: {fila['# of Hours']}\n\n"
            f"Máximo permitido: 8 horas"
        )

        mostrar_alerta(driver, mensaje)
        raise Exception("Cliente excede horas permitidas")

    # =========================
    # PROVIDERS - MAX 10 HORAS
    # =========================
    provider_dia = (
        excel
        .groupby(["Provider Name", "Date of Service"])["# of Hours"]
        .sum()
        .reset_index()
    )

    providers_excedidos = provider_dia[provider_dia["# of Hours"] > 10]

    if not providers_excedidos.empty:
        fila = providers_excedidos.iloc[0]

        mensaje = (
            f"ERROR DE HORAS (PROVIDER)\n\n"
            f"Provider: {fila['Provider Name']}\\n"
            f"Fecha: {fila['Date of Service'].strftime('%m/%d/%Y')}\n"
            f"Horas: {fila['# of Hours']}\n\n"
            f"Máximo permitido: 10 horas"
        )

        mostrar_alerta(driver, mensaje)
        raise Exception("Provider excede horas permitidas")

    print("✅ VALIDACIÓN OK — se puede continuar")

    usuarios_df = DF_AVILITY

    fila = usuarios_df.loc[usuarios_df["Usuario_App"] == usuario_app]

    user_ID = fila["Usuario"].iloc[0]
    password = fila["contrasena"].iloc[0]

    print(user_ID)
    print(password)
    enter_user = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.ID, "userId"))
    )

    enter_user.send_keys(user_ID)

    enter_password=driver.find_element(By.ID,value="password")
    enter_password.send_keys(password)

    encontrado=False

    while not encontrado:
        try:
            cookies = WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(., 'Accept') or contains(., 'Got')]")
                )
            )
            cookies.click()
            encontrado = True
            print("Cookies aceptadas")
        except:
            print("No encontrado, reintentando...")




    #--------------------------------------------Pagina Facturacion--------------------------------------------------------------------------
    progreso = cargar_progreso() or {}

    start_client = progreso.get("client_index", 0)
    start_provider = progreso.get("provider_index", 0)
    start_ciclo = progreso.get("ciclo", 0)

    archivo_guardado = progreso.get("nombre_billing")
    # Verificar si el archivo es diferente
    if archivo_guardado and archivo_guardado != archivo_actual:

        borrar = preguntar_archivo( archivo_guardado, archivo_actual)
        print("VALOR DE BORRAR:", borrar)
        if borrar:
            limpiar_progreso()
            print("BORRANDO")
            start_client = 0
            start_provider = 0
            start_ciclo = 0
        else:
            return

    clientes_unicos = excel["Client Name"].unique()
    primer_provider=True

    for cliente_i, client_name in enumerate(clientes_unicos):
        if cliente_i < start_client:
            continue
        fila = excel[excel["Client Name"] == client_name].copy()
        total_providers_cliente = fila["Provider Name"].count()

        providers_unicos = fila["Provider Name"].unique()

        for provider_i, provider in enumerate(providers_unicos):
         if cliente_i == start_client and provider_i < start_provider:
            continue
         ciclo = start_ciclo if (
                 cliente_i == start_client and provider_i == start_provider
         ) else 0
         cambio = False
         while cambio == False:
            print(provider)
            # --------------------------------------------------------------------------------------------
            # Copia segura del provider
            fila_provider = fila[fila["Provider Name"] == provider].copy()

            conteo = excel[(excel["Client Name"] == client_name) &
                           (excel["Provider Name"] == provider)].shape[0]
            # Convertir tipos sin warnings
            fila_provider["Authorization #"] = (
                fila_provider["Authorization #"]
                .fillna("")
                .apply(lambda x: str(int(x)) if str(x).replace('.0', '').isdigit() else str(x))
                .str.strip()
            )

            autorizaciones = fila_provider["Authorization #"].tolist()

            print(autorizaciones)
            conteo = fila_provider.shape[0]
            fila_provider["Date of Service"] = pd.to_datetime(fila_provider["Date of Service"])
            fechas = fila_provider["Date of Service"].dt.strftime("%m/%d/%Y").tolist()

            fila_provider["Billing Code"] = fila_provider["Billing Code"].astype(int)
            billingCodes = fila_provider["Billing Code"].tolist()

            fila_provider["Total Charges"] = fila_provider["Total Charges"].astype(float)
            charge = fila_provider["Total Charges"].tolist()

            fila_provider["# of Units"] = fila_provider["# of Units"].astype(float)
            unidades = fila_provider["# of Units"].tolist()

            fila_provider["Place of Service"] = fila_provider["Place of Service"].astype(str)
            place_services = fila_provider["Place of Service"].tolist()

            fila_provider["Agency Name"] = fila_provider["Agency Name"].astype(str)
            agency_name = fila_provider["Agency Name"].iloc[0].split()[0]

            fila_provider["Service"] = (
                fila_provider["Service"]
                .astype(str)
                .str.extract(r'(\d+)')  # extrae solo los dígitos
                .astype(int)
            )

            procedure_code = fila_provider["Service"].tolist()

            fila["Diagnosis Code"] = (
                fila["Diagnosis Code"]
                .astype(str)
                .str.replace(".", "", regex=False)
                .str.extract(r"([A-Z]\d{2,6})", expand=False)
            )

            diagnosis_code = fila["Diagnosis Code"].tolist()

            # ---------------- VALIDACION 97156 ----------------

            fila_provider["# of Hours"] = fila_provider["# of Hours"].astype(float)

            for _, row in fila_provider.iterrows():

                codigo = int(row["Billing Code"])
                horas = float(row["# of Hours"])

                if codigo == 97156 and horas > 1:
                    mensaje = (
                        "⚠ ERROR DE VALIDACION\n\n"
                        "El código 97156 NO puede superar 1 hora.\n\n"
                        f"Cliente: {client_name}\n"
                        f"Provider: {provider}\n"
                        f"Horas registradas: {horas}"
                    )

                    mostrar_alerta(driver, mensaje)
                    time.sleep(2)

                    raise Exception("Validación 97156 fallida")
            #--------------------------------------------------------------------------------------------

            def entrar_al_iframe_seguro(driver):
                max_intentos_globales = 30
                for intento in range(max_intentos_globales):
                    try:
                        # 1. Volver siempre a la raíz de la página
                        driver.switch_to.default_content()

                        # 2. Esperar a que el iframe tenga el 'src' de claims
                        # Usamos un selector CSS que es más rápido que XPath para esto
                        iframe_selector = "iframe#newBodyFrame[src*='claims-ui']"
                        WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, iframe_selector))
                        )

                        # 3. Cambiar al contexto del iframe
                        # Intentamos el switch por ID directamente
                        WebDriverWait(driver, 5).until(
                            EC.frame_to_be_available_and_switch_to_it((By.ID, "newBodyFrame"))
                        )

                        # 4. Esperar al elemento interno 'transactionType'
                        # Aumentamos el tiempo de espera por si la red está lenta
                        claimType = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.NAME, "transactionType"))
                        )

                        # Si llegamos aquí, el elemento existe. Interactuamos:
                        claimType.click()
                        claimType.send_keys("Professional Claim")
                        print("Formulario de Reclamos detectado con éxito.")
                        return True  # Éxito total

                    except (TimeoutException, StaleElementReferenceException) as e:
                        print(f"Intento {intento + 1} fallido. Reintentando switch de iframe...")
                        time.sleep(2)  # Pausa táctica para que el DOM se estabilice

                raise Exception("No se pudo encontrar el formulario 'transactionType' después de varios intentos.")
            # --- USO EN TU SCRIPT ---
            # Llama a esta función dentro de tu bucle, justo donde antes tenías el switch
            entrar_al_iframe_seguro(driver)

            first_option = WebDriverWait(driver, 20).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "li.MuiAutocomplete-option"))
            )

            first_option.click()

            payer = WebDriverWait(driver, 100).until(
                EC.presence_of_element_located((By.NAME, "payer"))
            )

            seguro = fila_provider["Funder"].iloc[0]

            palabras = str(seguro).split()
            seguro_corto = " ".join(palabras[:1]) if len(palabras) >= 1 else str(seguro)

            payer.click()
            payer.clear()
            payer.send_keys(seguro_corto)

            payer.send_keys(Keys.DOWN)
            payer.send_keys(Keys.ENTER)

            WebDriverWait(driver, 99999).until(
                EC.invisibility_of_element(first_option)
            )


            select_patient = WebDriverWait(driver, 99999).until(
                EC.element_to_be_clickable((By.XPATH,
                                            "/html/body/div[1]/div/div/div[3]/div/form/div[1]/div[1]/div[1]/div[1]/div[2]/div/div[1]/div/div/input"))
            )

            select_patient.send_keys(client_name)
            try:
                time.sleep(3)

                if select_patient.is_displayed():
                    select_patient.send_keys(Keys.DOWN)
                    select_patient.send_keys(Keys.ENTER)

            except Exception:
                pass  # sigue el código sin interrumpir

            WebDriverWait(driver, 20).until(
                lambda d: d.find_element(By.NAME, "subscriber.memberId").get_attribute("value").strip() != ""
            )
            subscriber_memberId= driver.find_element(By.NAME, "subscriber.memberId")
            subscriber_memberId =  subscriber_memberId.get_attribute("value")



            authorized_plan= driver.find_element(By.NAME,value="claimInformation.benefitsAssignmentCertification")
            authorized_plan.send_keys("Y")


            autocompletar("/html/body/div[1]/div/div/div[3]/div/form/div[1]/div[1]/div[2]/div[1]/div[2]/div/div[1]/div/div/div/input",f"{agency_name}","formulario")
            print(agency_name, seguro)


            if seguro == "Molina Healthcare of Nevada" and agency_name=="Spectrum":
                direccion = driver.find_element(By.NAME, "billingProvider.addressLine1")
                direccion.send_keys(Keys.CONTROL + "a")  # selecciona todo
                direccion.send_keys(Keys.DELETE)
                direccion.send_keys("7880 W MAULE AVE UNIT 1070")

                ciudad = driver.find_element(By.NAME, "billingProvider.city")
                ciudad.send_keys(Keys.CONTROL + "a")  # selecciona todo
                ciudad.send_keys(Keys.DELETE)
                ciudad.send_keys("LAS VEGAS")

                estado = driver.find_element(By.NAME, "billingProvider.stateCode")
                estado.send_keys(Keys.CONTROL + "a")  # selecciona todo
                estado.send_keys(Keys.DELETE)
                estado.send_keys("Nevada")

                postal=driver.find_element(By.NAME, "billingProvider.zipCode")
                postal.send_keys(Keys.CONTROL + "a")  # selecciona todo
                postal.send_keys(Keys.DELETE)
                postal.send_keys("891135283")
            def reescribir(valor, texto):
                elemento = driver.find_element(By.NAME,
                                                       value=f"{valor}")

                elemento.click()
                elemento.send_keys(Keys.CONTROL, "a")
                elemento.send_keys(Keys.BACKSPACE)
                elemento.send_keys(texto)



            button_rendering_provider=driver.find_element(By.XPATH,value="/html/body/div[1]/div/div/div[3]/div/form/div[1]/div[1]/div[2]/div[3]/button[1]")
            button_rendering_provider.click()

            last_name_rendering = " ".join(provider.split()[-2:])

            autocompletar("/html/body/div[1]/div/div/div[3]/div/form/div[1]/div[1]/div[2]/div[2]/div/div[2]/div/div[1]/div/div/div/div/input", last_name_rendering,"formulario")


            button_refering_provider=driver.find_element(By.XPATH,value="/html/body/div[1]/div/div/div[3]/div/form/div[1]/div[1]/div[2]/div[3]/button[2]")
            button_refering_provider.click()
            first_name_referring=fila["Referring Provider Name"].iloc[0].split()[0]
            last_name_referring = fila["Referring Provider Name"].iloc[0].split()[-1]

            excel = excel.dropna(subset=["Referring Provider NPI"])
            excel["Referring Provider NPI"] = excel["Referring Provider NPI"].astype(int)
            referring_npi = int(fila["Referring Provider NPI"].iloc[0])


            campo_last_name=driver.find_element(By.NAME,value="claimInformation.referringProvider.lastName")
            campo_first_name=driver.find_element(By.NAME,value="claimInformation.referringProvider.firstName")
            campo_npi=driver.find_element(By.NAME,value="claimInformation.referringProvider.npi")
            campo_last_name.send_keys(last_name_referring)
            campo_first_name.send_keys(first_name_referring)
            campo_npi.send_keys(f"{referring_npi}")


            patient_control_number=driver.find_element(By.NAME,value="claimInformation.controlNumber")
            patient_control_number.send_keys(subscriber_memberId)

            autocompletar("claimInformation.providerAcceptAssignmentCode","A", "formulario_Nombre")
            autocompletar("claimInformation.placeOfServiceCode",place_services[0], "formulario_Nombre")
            autocompletar("claimInformation.frequencyTypeCode","A", "formulario_Nombre")


            relase = driver.find_element(By.NAME,
                                         value="claimInformation.informationReleaseCode")
            relase.send_keys("Y")

            time.sleep(0.5)
            options = WebDriverWait(driver, 10).until(
                EC.visibility_of_all_elements_located((By.CSS_SELECTOR, "li.MuiAutocomplete-option"))
            )

            options[1].click()

            autocompletar("claimInformation.providerSignatureOnFile", "Y","formulario_Nombre")


            elemento = driver.find_element(By.NAME,
                                           value="payer.claimFilingIndicatorCode")

            elemento.click()
            elemento.send_keys(Keys.CONTROL, "a")
            elemento.send_keys(Keys.BACKSPACE)
            autocompletar("payer.claimFilingIndicatorCode","mc","formulario_Nombre")
            autocompletar("claimInformation.diagnoses.0.code",f"{diagnosis_code[0]}","formulario_Nombre")

            autorizacion = driver.find_element(By.NAME, value="claimInformation.priorAuthorizationNumber")
            autorizacion.send_keys(autorizaciones[ciclo])

            continuar=True
            posicion = 0
            repeticion=0
            while conteo>ciclo and continuar:
                if conteo-ciclo==1:
                    repeticion+=1
                print("--------------------------------------------------")
                print(f"resta {conteo-ciclo}")
                print(f"posicion {posicion}")
                print(f"ciclo {ciclo}")
                print(f"conteo {conteo}")
                campo_from_date = driver.find_element(By.NAME, f"claimInformation.serviceLines.{posicion}.fromDate")
                campo_from_date.clear()
                campo_from_date.send_keys(fechas[ciclo])

                campo_service_date = driver.find_element(By.NAME, f"claimInformation.serviceLines.{posicion}.toDate")
                campo_service_date.clear()
                campo_service_date.send_keys(fechas[ciclo])

                campo_place=driver.find_element(By.NAME,value=f"claimInformation.serviceLines.{posicion}.placeOfServiceCode")
                campo_place.send_keys(place_services[ciclo])


                campo_procedure_code=driver.find_element(By.NAME,value=f"claimInformation.serviceLines.{posicion}.procedureCode")
                if procedure_code[ciclo]==97153:

                    campo_procedure_code.send_keys("97153")

                    time.sleep(1)
                    first_option = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "li.MuiAutocomplete-option"))
                    )
                    first_option.click()
                    campo_procedure_code.send_keys()


                    modificador=driver.find_element(By.NAME,value=f"claimInformation.serviceLines.{posicion}.modifierCode1")
                    modificador.send_keys("UD")

                else:

                    campo_procedure_code.send_keys(f"{procedure_code[ciclo]}")

                    time.sleep(1)
                    first_option = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "li.MuiAutocomplete-option"))
                    )
                    first_option.click()
                    campo_procedure_code.send_keys()

                autocompletar(f"claimInformation.serviceLines.{posicion}.diagnosisCodePointer1",f"{diagnosis_code[0]}","factura")
                campo_chargue_amount=driver.find_element(By.NAME,value=f"claimInformation.serviceLines.{posicion}.amount")
                campo_chargue_amount.send_keys(f"{charge[ciclo]}")

                campo_quantity=driver.find_element(By.NAME,value= f"claimInformation.serviceLines.{posicion}.quantity")
                campo_quantity.send_keys(f"{unidades[ciclo]}")
                if ciclo+1<conteo:
                    if(autorizaciones[ciclo]!=autorizaciones[ciclo+1]):
                        mensaje = (
                            "⚠️ AVISO IMPORTANTE ⚠️\n\n"
                            "El número de autorización cambia a partir de este punto.\n\n"
                            "Cuando termines esta facturación,\n"
                            "vuelve a cargar la página de Professional Claim."
                        )
                        mostrar_alerta(driver, mensaje)
                        WebDriverWait(driver, 999999).until_not(EC.alert_is_present())

                        ciclo += 1
                        posicion +=1
                        continuar=False
                        guardar_progreso(cliente_i, provider_i, ciclo,archivo_actual)
                    else:
                        if conteo - ciclo != 1:
                            add_line_button = driver.find_element(By.XPATH,
                                                                  value="/html/body/div[1]/div/div/div[3]/div/form/div[1]/div[4]/div[2]/div/div[2]/div[1]/button")
                            add_line_button.click()
                        ciclo += 1
                        posicion += 1
                        guardar_progreso(cliente_i, provider_i, ciclo,archivo_actual )
                if repeticion == 1:
                    ciclo += 1
                    guardar_progreso(cliente_i, provider_i, ciclo,archivo_actual)

                if conteo==ciclo:
                    cambio = True
                    mensaje = (
                        "✔️ FACTURACIÓN RELLENADA\n\n"
                        "La facturación fue rellenada correctamente.\n\n"
                        "Cuando estés listo, continúa y ve a Claim Prof."

                    )
                    mostrar_alerta(driver, mensaje)
                    WebDriverWait(driver, 999999).until_not(EC.alert_is_present())

            WebDriverWait(driver, 9999).until(
                EC.url_changes(driver.current_url)
            )
            continue_button = driver.find_element(By.XPATH,
                                                  "/html/body/div/div/div/div[2]/div/div[3]/button[4]")

            WebDriverWait(driver, 999999).until(
                EC.staleness_of(continue_button))
            if continuar==True:
                guardar_progreso(cliente_i, provider_i + 1, 0,archivo_actual)


    mensaje = (
        "✔️ PROCESO COMPLETADO\n\n"
        "Todos los clientes fueron facturados correctamente."
    )
    mostrar_alerta(driver, mensaje)
    WebDriverWait(driver, 999999).until_not(EC.alert_is_present())
    limpiar_progreso()
    print("✅ Facturación completada desde cero")