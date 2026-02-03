from time import sleep
from tkinter import Tk, filedialog
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import pandas as pd
import time
import json
import os
PROGRESO_FILE = "progreso_facturacion.json"



def medicaid_facturacion(excel_trabajadores, excel_billing,usuario_app):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option("detach", True)
    #
    def mostrar_alerta(driver, mensaje):
        driver.execute_script("alert(arguments[0]);", mensaje)
    # Leer archivo CSV


    def guardar_progreso(client_index, provider_index, ciclo):
        data = {
            "client_index": client_index,
            "provider_index": provider_index,
            "ciclo": ciclo
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


    usuarios_df = pd.read_excel("medicaid-Usuarios.xlsx")

    fila = usuarios_df.loc[usuarios_df["Usuario_App"] == usuario_app]

    usuario_inicio = fila["Usuario"].iloc[0]
    contrasena_inicio = fila["contrasena"].iloc[0]

    print(usuario_inicio)
    print(contrasena_inicio)
    #-----------------------------------------------------------------------------------
    npi_table = excel_trabajadores
    excel = excel_billing

    print(excel["Client Name"].unique())
    billing = excel.merge(npi_table, on="Provider Name", how="left")






    total_clientes = excel["Client Name"].nunique()

    #------------------------------------------------------------------------------------------------
    # Agrupar por cliente y contar proveedores distintos
    conteo_por_cliente = excel.groupby("Client Name")["Provider Name"].nunique().reset_index(name="Num_Providers")
    # Calcular el total de proveedores distintos sumando todos
    total_providers = conteo_por_cliente["Num_Providers"].sum()
    #------------------------------------------------------------------------------------------------

    print(total_providers)
    driver = webdriver.Chrome(options=chrome_options)
    driver.get("https://www.medicaid.nv.gov/hcp/provider/Home/tabid/135/Default.aspx")

    usuario= driver.find_element(By.XPATH,value="/html/body/form/div[3]/div/div[2]/div[3]/div[2]/table/tbody/tr/td/table/tbody/tr[2]/td[1]/div[1]/div/div/div/div[1]/div[2]/div[1]/div/div[2]/input")
    usuario.send_keys(usuario_inicio)

    contrasena= driver.find_element(By.XPATH,value="/html/body/form/div[3]/div/div[2]/div[3]/div[2]/table/tbody/tr/td/table/tbody/tr[2]/td[1]/div[1]/div/div/div/div[1]/div[2]/div[2]/div/div[2]/input")
    contrasena.send_keys(contrasena_inicio)

    #--------------------------------------------------------------------------------------------PAGINA 1--------------------------------------------------------------------------------------------------------------

    clientes_unicos = excel["Client Name"].unique()
    no_repetir=False
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

    progreso = cargar_progreso()

    start_client = progreso["client_index"] if progreso else 0
    start_provider = progreso["provider_index"] if progreso else 0
    start_ciclo = progreso["ciclo"] if progreso else 0

    print("✅ VALIDACIÓN OK — se puede continuar")
    for cliente_i, client_name in enumerate(clientes_unicos):
        if cliente_i < start_client:
            continue
        fila = excel[excel["Client Name"] == client_name]
        total_providers_cliente = fila["Provider Name"].count()

        providers_unicos = fila["Provider Name"].unique()
        for provider_i, provider in enumerate(providers_unicos):
            if cliente_i == start_client and provider_i < start_provider:
                continue
            WebDriverWait(driver, 999999).until(
                EC.presence_of_element_located((By.XPATH, "/html/body/form/div[3]/div/div[2]/div[3]/div[2]/table/tbody/tr/td/table/tbody/tr[2]/td[2]/div/div/div/div[1]/div/div[1]/div[2]/div/div[4]/div[3]/div[1]/div/div[2]/input"))
            )

            fila = excel[(excel["Client Name"] == client_name) &
                         (excel["Provider Name"] == provider)]

            conteo = excel[(excel["Client Name"] == client_name) &
                           (excel["Provider Name"] == provider)].shape[0]

            print(f"Total provider client: {total_providers_cliente}")
            print(conteo)
            print(client_name)
            # -------------------------------------------------------------------------------------------------------
            excel = excel.dropna(subset=["Referring Provider NPI"])
            excel["Referring Provider NPI"] = excel["Referring Provider NPI"].astype(int)
            Refering_Provider_NPI = int(fila["Referring Provider NPI"].iloc[0])
            print(Refering_Provider_NPI)


            # -------------------------------------------------------------------------------------------------------
            # ------------------------------------------------------------------------------------------



            fila["Date of Service"] = pd.to_datetime(fila["Date of Service"])
            fechas = fila["Date of Service"].dt.strftime("%m/%d/%Y").tolist()

            # --------------------------------------------------------------------------------------------------------


            fila["Billing Code"] = fila["Billing Code"].astype(int)

            Billing_Codes = fila["Billing Code"].tolist()

            # --------------------------------------------------------------------------------------------

            # Asegurarse de que la columna sea numérica
            fila["Total Charges"] = fila["Total Charges"].astype(float)

            # Guardar todos los charges en una lista
            Charge = fila["Total Charges"].tolist()

            # --------------------------------------------------------------------------------------------

            fila["Authorization #"] = fila["Authorization #"].astype(int)


            autorizaciones = fila["Authorization #"].tolist()
            # ------------------------------------------------------------------------------------------------------


            fila["# of Units"] = fila["# of Units"].astype(float)
            Unidades = fila["# of Units"].tolist()


            fila["Place of Service"] = fila["Place of Service"].astype(str)
            place_services = fila["Place of Service"].tolist()
            # -----------------------------------------------------------------------------------------------
            excel = excel.dropna(subset=["Insured's ID"])
            excel["Insured's"] = excel["Insured's ID"].astype(int)
            Insured_ID = int(fila["Insured's ID"].iloc[0])



            # ------------------------------------------------------------------------------------------------

            excel = excel.dropna(subset=["Authorization #"])
            excel["Authorization #"] = excel["Authorization #"].astype(int)
            Authorization = int(fila["Authorization #"].iloc[0])

            fila = billing[(billing["Client Name"] == client_name) &
                           (billing["Provider Name"] == provider)]

            # Tomar el NPI de esa fila
            try:
                provider_NPI = int(fila["NPI"].dropna().iloc[0])
            except IndexError:
                driver.execute_script("""
                     var div = document.createElement('div');
                     div.innerHTML = '⚠️ No encuentro a ese trabajador';
                     div.style.position = 'fixed';
                     div.style.top = '20px';
                     div.style.left = '50%';
                     div.style.transform = 'translateX(-50%)';
                     div.style.background = 'yellow';   
                     div.style.padding = '10px';
                     div.style.border = '2px solid black';
                     div.style.zIndex = 9999;
                     div.style.fontSize = '20px';           // tamaño de letra más grande
                     div.style.fontWeight = 'bold';         // opcional: texto en negrita
                     document.body.appendChild(div);
                     """)

            # ------------------------------------------------------------------------------------------------


            print(provider)
            print(f"0000{Insured_ID}")
            print(f"TOTAL CLIENTES {total_clientes}")
            print(Authorization)
            print(Charge)
            print(Unidades)

            def writeRef():
                Refering_Provider_NPI_Write = driver.find_element(By.XPATH,value="/html/body/form/div[3]/div/div[2]/div[3]/div[2]/table/tbody/tr/td/table/tbody/tr[2]/td[2]/div/div/div/div[1]/div/div[1]/div[2]/div/div[4]/div[5]/div[1]/div/div[2]/input")
                Refering_Provider_NPI_Write.send_keys(f"{Refering_Provider_NPI}")

            rendering_provider_ID_Write = driver.find_element(By.XPATH, "/html/body/form/div[3]/div/div[2]/div[3]/div[2]/table/tbody/tr/td/table/tbody/tr[2]/td[2]/div/div/div/div[1]/div/div[1]/div[2]/div/div[4]/div[3]/div[1]/div/div[2]/input")
            rendering_provider_ID_Write.send_keys(f"{provider_NPI}")


            writeRef()
            time.sleep(1)
            writeRef()



            writeAuth= driver.find_element(By.XPATH, value="/html/body/form/div[3]/div/div[2]/div[3]/div[2]/table/tbody/tr/td/table/tbody/tr[2]/td[2]/div/div/div/div[1]/div/div[1]/div[2]/div/div[9]/div[3]/div[2]/div/div[2]/input")
            writeAuth.send_keys(f"{Authorization}")


            NPI_Rendering = driver.find_element(By.XPATH, "/html/body/form/div[3]/div/div[2]/div[3]/div[2]/table/tbody/tr/td/table/tbody/tr[2]/td[2]/div/div/div/div[1]/div/div[1]/div[2]/div/div[4]/div[3]/div[3]/div/div[2]/select")
            select = Select(NPI_Rendering)
            select.select_by_index(1)

            NPI_Refering = driver.find_element(By.XPATH, "/html/body/form/div[3]/div/div[2]/div[3]/div[2]/table/tbody/tr/td/table/tbody/tr[2]/td[2]/div/div/div/div[1]/div/div[1]/div[2]/div/div[4]/div[5]/div[3]/div/div[2]/select")
            select = Select(NPI_Refering)
            select.select_by_index(1)


            transport_C= driver.find_element(By.XPATH, value="/html/body/form/div[3]/div/div[2]/div[3]/div[2]/table/tbody/tr/td/table/tbody/tr[2]/td[2]/div/div/div/div[1]/div/div[1]/div[2]/div/div[9]/div[4]/div/div/div/div[2]/table/tbody/tr/td[2]/input")
            transport_C.click()

            time.sleep(2)
            writeID= driver.find_element(By.XPATH,value="/html/body/form/div[3]/div/div[2]/div[3]/div[2]/table/tbody/tr/td/table/tbody/tr[2]/td[2]/div/div/div/div[1]/div/div[1]/div[2]/div/div[6]/div[1]/div/div/div[2]/input")
            writeID.send_keys(f"0000{Insured_ID}")
            writeID= driver.find_element(By.XPATH,value="/html/body/form/div[3]/div/div[2]/div[3]/div[2]/table/tbody/tr/td/table/tbody/tr[2]/td[2]/div/div/div/div[1]/div/div[1]/div[2]/div/div[9]/div[3]/div[1]/div/div[2]/input")
            writeID.send_keys(f"0000{Insured_ID}")

            #------------------------------------------------------------------------FIN PAGINA 1------------------------------------------------------------------------------------

            #-----------------------------------------------------------------------PAGINA 2------------------------------------------------------------------------------------------
            # Aquí esperamos a que aparezca un elemento que solo existe después de autenticarse
            WebDriverWait(driver, 9999999).until(
                EC.presence_of_element_located((By.XPATH, "/html/body/form/div[3]/div/div[2]/div[3]/div[2]/table/tbody/tr/td/table/tbody/tr[2]/td[2]/div/div/div/div[1]/div[3]/div[1]/div/div/div[2]/div[2]/table/tbody/tr[5]/td/div/div/div/div[1]/div[3]/div/div[2]/input"))
            )

            Diagnostico= driver.find_element(By.XPATH,value="/html/body/form/div[3]/div/div[2]/div[3]/div[2]/table/tbody/tr/td/table/tbody/tr[2]/td[2]/div/div/div/div[1]/div[3]/div[1]/div/div/div[2]/div[2]/table/tbody/tr[5]/td/div/div/div/div[1]/div[3]/div/div[2]/input")
            Diagnostico.send_keys("F840-Autistic disorder")

            add_diagnostico=driver.find_element(By.XPATH, value="/html/body/form/div[3]/div/div[2]/div[3]/div[2]/table/tbody/tr/td/table/tbody/tr[2]/td[2]/div/div/div/div[1]/div[3]/div[1]/div/div/div[2]/div[2]/table/tbody/tr[5]/td/div/div/div/div[2]/div/a[1]")
            add_diagnostico.click()
            #-----------------------------------------------------------------------FIN PAGINA 2------------------------------------------------------------------------------------------

            #-----------------------------------------------------------------------PAGINA 3------------------------------------------------------------------------------------------

            WebDriverWait(driver, 99999).until(
                    EC.presence_of_element_located((By.XPATH, "/html/body/form/div[3]/div/div[2]/div[3]/div[2]/table/tbody/tr/td/table/tbody/tr[2]/td[2]/div/div/div/div[1]/div[5]/div/div/div/div[2]/div[2]/table/tbody/tr[5]/td/div/div/div[1]/div[1]/div[2]/div/div[2]/input[1]"))
            )



            ciclo=0
            pos = 0
            while ciclo <conteo:
                time.sleep(4)
                if ciclo>0 and autorizaciones[ciclo]!=autorizaciones[ciclo-1]:
                    mensaje = (
                        "⚠️ AVISO IMPORTANTE ⚠️\n\n"
                        "El número de autorización cambia a partir de este punto.\n\n"
                        "Cuando termines esta facturación,\n"
                        "vuelve a cargar la página de Professional Claim."
                    )
                    mostrar_alerta(driver, mensaje)
                    WebDriverWait(driver, 999999).until_not(EC.alert_is_present())

                    WebDriverWait(driver, 99999).until(
                        EC.presence_of_element_located((By.XPATH,
                                                        "/html/body/form/div[3]/div/div[2]/div[3]/div[2]/table/tbody/tr/td/table/tbody/tr[2]/td[2]/div/div/div/div[1]/div/div[1]/div[2]/div/div[4]/div[3]/div[1]/div/div[2]/input"))
                    )

                    fila = excel[(excel["Client Name"] == client_name) &
                                 (excel["Provider Name"] == provider)]

                    conteo = excel[(excel["Client Name"] == client_name) &
                                   (excel["Provider Name"] == provider)].shape[0]

                    print(f"Total provider client: {total_providers_cliente}")
                    print(conteo)
                    print(client_name)
                    # -------------------------------------------------------------------------------------------------------
                    excel = excel.dropna(subset=["Referring Provider NPI"])
                    excel["Referring Provider NPI"] = excel["Referring Provider NPI"].astype(int)
                    Refering_Provider_NPI = int(fila["Referring Provider NPI"].iloc[0])
                    print(Refering_Provider_NPI)

                    # -------------------------------------------------------------------------------------------------------
                    # ------------------------------------------------------------------------------------------

                    # excel["Date of Service"] = pd.to_datetime(excel["Date of Service"])
                    # excel["Date of Service (str)"] = excel["Date of Service"].dt.strftime("%m/%d/%Y")
                    # Date = fila["Date of Service"].iloc[0].strftime("%m/%d/%Y")

                    fila["Date of Service"] = pd.to_datetime(fila["Date of Service"])
                    fechas = fila["Date of Service"].dt.strftime("%m/%d/%Y").tolist()

                    # --------------------------------------------------------------------------------------------------------
                    # excel = excel.dropna(subset=["Billing Code"])
                    # excel["Billing Code"] = excel["Billing Code"].astype(int)
                    # Billing_Code = int(fila["Billing Code"].iloc[0])

                    fila["Billing Code"] = fila["Billing Code"].astype(int)

                    # Guardar todos los charges en una lista
                    Billing_Codes = fila["Billing Code"].tolist()

                    # --------------------------------------------------------------------------------------------
                    # excel = excel.dropna(subset=["Total Charges"])
                    # excel["Total Charges"] = excel["Total Charges"].astype(float)
                    # Charge = float(fila["Total Charges"].iloc[0])

                    # Asegurarse de que la columna sea numérica
                    fila["Total Charges"] = fila["Total Charges"].astype(float)

                    # Guardar todos los charges en una lista
                    Charge = fila["Total Charges"].tolist()

                    # --------------------------------------------------------------------------------------------
                    # Asegurarse de que la columna sea numérica
                    fila["Authorization #"] = fila["Authorization #"].astype(int)

                    # Guardar todos los charges en una lista
                    autorizaciones = fila["Authorization #"].tolist()
                    # ------------------------------------------------------------------------------------------------------
                    # excel = excel.dropna(subset=["# of Units"])
                    # excel["# of Units"] = excel["# of Units"].astype(float)
                    # Unidades = float(fila["# of Units"].iloc[0])

                    # Asegurarse de que la columna sea numérica
                    fila["# of Units"] = fila["# of Units"].astype(float)

                    # Guardar todos los charges en una lista
                    Unidades = fila["# of Units"].tolist()

                    fila["Place of Service"] = fila["Place of Service"].astype(str)

                    place_services = fila["Place of Service"].tolist()
                    # -----------------------------------------------------------------------------------------------
                    excel = excel.dropna(subset=["Insured's ID"])
                    excel["Insured's"] = excel["Insured's ID"].astype(int)
                    Insured_ID = int(fila["Insured's ID"].iloc[0])

                    # ------------------------------------------------------------------------------------------------


                    Authorization =autorizaciones[ciclo]

                    fila = billing[(billing["Client Name"] == client_name) &
                                   (billing["Provider Name"] == provider)]

                    # Tomar el NPI de esa fila
                    provider_NPI = int(fila["NPI"].iloc[0])

                    # ------------------------------------------------------------------------------------------------

                    print(provider)
                    print(f"0000{Insured_ID}")
                    print(f"TOTAL CLIENTES {total_clientes}")
                    print(Authorization)
                    print(Charge)
                    print(Unidades)


                    # def writeRef():
                    #     Refering_Provider_NPI_Write = driver.find_element(By.XPATH,
                    #                                                       value="/html/body/form/div[3]/div/div[2]/div[3]/div[2]/table/tbody/tr/td/table/tbody/tr[2]/td[2]/div/div/div/div[1]/div/div[1]/div[2]/div/div[4]/div[5]/div[1]/div/div[2]/input")
                    #     Refering_Provider_NPI_Write.send_keys(f"{Refering_Provider_NPI}")


                    rendering_provider_ID_Write = driver.find_element(By.XPATH,
                                                                      "/html/body/form/div[3]/div/div[2]/div[3]/div[2]/table/tbody/tr/td/table/tbody/tr[2]/td[2]/div/div/div/div[1]/div/div[1]/div[2]/div/div[4]/div[3]/div[1]/div/div[2]/input")
                    rendering_provider_ID_Write.send_keys(f"{provider_NPI}")

                    writeRef()
                    time.sleep(1)
                    writeRef()

                    writeAuth = driver.find_element(By.XPATH,
                                                    value="/html/body/form/div[3]/div/div[2]/div[3]/div[2]/table/tbody/tr/td/table/tbody/tr[2]/td[2]/div/div/div/div[1]/div/div[1]/div[2]/div/div[9]/div[3]/div[2]/div/div[2]/input")
                    writeAuth.send_keys(f"{Authorization}")

                    NPI_Rendering = driver.find_element(By.XPATH,
                                                        "/html/body/form/div[3]/div/div[2]/div[3]/div[2]/table/tbody/tr/td/table/tbody/tr[2]/td[2]/div/div/div/div[1]/div/div[1]/div[2]/div/div[4]/div[3]/div[3]/div/div[2]/select")
                    select = Select(NPI_Rendering)
                    select.select_by_index(1)

                    NPI_Refering = driver.find_element(By.XPATH,
                                                       "/html/body/form/div[3]/div/div[2]/div[3]/div[2]/table/tbody/tr/td/table/tbody/tr[2]/td[2]/div/div/div/div[1]/div/div[1]/div[2]/div/div[4]/div[5]/div[3]/div/div[2]/select")
                    select = Select(NPI_Refering)
                    select.select_by_index(1)

                    transport_C = driver.find_element(By.XPATH,
                                                      value="/html/body/form/div[3]/div/div[2]/div[3]/div[2]/table/tbody/tr/td/table/tbody/tr[2]/td[2]/div/div/div/div[1]/div/div[1]/div[2]/div/div[9]/div[4]/div/div/div/div[2]/table/tbody/tr/td[2]/input")
                    transport_C.click()

                    time.sleep(1)
                    writeID = driver.find_element(By.XPATH,
                                                  value="/html/body/form/div[3]/div/div[2]/div[3]/div[2]/table/tbody/tr/td/table/tbody/tr[2]/td[2]/div/div/div/div[1]/div/div[1]/div[2]/div/div[6]/div[1]/div/div/div[2]/input")
                    writeID.send_keys(f"0000{Insured_ID}")
                    writeID = driver.find_element(By.XPATH,
                                                  value="/html/body/form/div[3]/div/div[2]/div[3]/div[2]/table/tbody/tr/td/table/tbody/tr[2]/td[2]/div/div/div/div[1]/div/div[1]/div[2]/div/div[9]/div[3]/div[1]/div/div[2]/input")
                    writeID.send_keys(f"0000{Insured_ID}")
                    # ------------------------------------------------------------------------FIN PAGINA 1------------------------------------------------------------------------------------

                    # -----------------------------------------------------------------------PAGINA 2------------------------------------------------------------------------------------------
                    # Aquí esperamos a que aparezca un elemento que solo existe después de autenticarse
                    WebDriverWait(driver, 99999).until(
                        EC.presence_of_element_located((By.XPATH,
                                                        "/html/body/form/div[3]/div/div[2]/div[3]/div[2]/table/tbody/tr/td/table/tbody/tr[2]/td[2]/div/div/div/div[1]/div[3]/div[1]/div/div/div[2]/div[2]/table/tbody/tr[5]/td/div/div/div/div[1]/div[3]/div/div[2]/input"))
                    )

                    Diagnostico = driver.find_element(By.XPATH,
                                                      value="/html/body/form/div[3]/div/div[2]/div[3]/div[2]/table/tbody/tr/td/table/tbody/tr[2]/td[2]/div/div/div/div[1]/div[3]/div[1]/div/div/div[2]/div[2]/table/tbody/tr[5]/td/div/div/div/div[1]/div[3]/div/div[2]/input")
                    Diagnostico.send_keys("F840-Autistic disorder")

                    add_diagnostico = driver.find_element(By.XPATH,
                                                          value="/html/body/form/div[3]/div/div[2]/div[3]/div[2]/table/tbody/tr/td/table/tbody/tr[2]/td[2]/div/div/div/div[1]/div[3]/div[1]/div/div/div[2]/div[2]/table/tbody/tr[5]/td/div/div/div/div[2]/div/a[1]")
                    add_diagnostico.click()
                    # -----------------------------------------------------------------------FIN PAGINA 2------------------------------------------------------------------------------------------

                    # -----------------------------------------------------------------------PAGINA 3------------------------------------------------------------------------------------------

                    WebDriverWait(driver, 99999).until(
                        EC.presence_of_element_located((By.XPATH,
                                                        "/html/body/form/div[3]/div/div[2]/div[3]/div[2]/table/tbody/tr/td/table/tbody/tr[2]/td[2]/div/div/div/div[1]/div[5]/div/div/div/div[2]/div[2]/table/tbody/tr[5]/td/div/div/div[1]/div[1]/div[2]/div/div[2]/input[1]"))
                    )

                    num_factura = 0
                    while ciclo < conteo:
                        time.sleep(4)

                        fecha1 = driver.find_element(By.ID,
                                                     value=f"dnn_ctr724_SubmitProfessionalClaim3_ServiceDetailsDataList_SDDetailFromDateCmnDate_{num_factura}_Control_{num_factura}")
                        driver.execute_script(f"arguments[0].value = '{fechas[ciclo]}';", fecha1)

                        fecha2 = driver.find_element(By.ID,
                                                     value=f"dnn_ctr724_SubmitProfessionalClaim3_ServiceDetailsDataList_SDDetailToDateCmnDate_{num_factura}_Control_{num_factura}")
                        driver.execute_script(f"arguments[0].value = '{fechas[ciclo]}';", fecha2)

                        Place = driver.find_element(By.ID,
                                                    f"dnn_ctr724_SubmitProfessionalClaim3_ServiceDetailsDataList_SDDetailPlaceOfServiceCmnDropDownList_{num_factura}_Control_{num_factura}")
                        select = Select(Place)
                        # print(f"Place {place_services[ciclo]}")
                        if place_services[num_factura]=="12":
                            select.select_by_index(12)
                        else:
                            select.select_by_index(3)
                        print(Billing_Codes[ciclo])


                        suma_charges = 0
                        suma_unidades=0
                        sumas=0
                        # Contar cuántas veces aparece la combinación fecha + billing code
                        ocurrencias = sum(
                            1 for j in range(len(fechas))
                            if fechas[j] == fechas[ciclo] and Billing_Codes[j] == Billing_Codes[ciclo]
                        )

                        # Solo sumar si ocurre exactamente 2 veces
                        if ocurrencias == 2:
                            for i in range(len(fechas)):
                                if fechas[i] == fechas[ciclo] and Billing_Codes[i] == Billing_Codes[ciclo]:
                                    suma_charges += Charge[i]
                                    suma_unidades += Unidades[i]



                        Procedure_Code = driver.find_element(By.ID,
                                                             value=f"dnn_ctr724_SubmitProfessionalClaim3_ServiceDetailsDataList_SDDetailProcedureCodeCmnTextBox_{num_factura}_Control_{num_factura}")
                        Procedure_Code.send_keys(f"{Billing_Codes[ciclo]}")
                        time.sleep(1)

                        # Selecciona la primera sugerencia
                        Procedure_Code.send_keys(Keys.ARROW_DOWN)
                        Procedure_Code.send_keys(Keys.ENTER)


                        if str(Billing_Codes[ciclo]) == "97153":
                            Modifier = driver.find_element(By.ID,
                                                           value=f"dnn_ctr724_SubmitProfessionalClaim3_ServiceDetailsDataList_SDDetailModifier1CmnTextBox_{num_factura}_Control_{num_factura}")
                            Modifier.send_keys("UD-M/CAID CARE LEV 13 STATE DEF")

                        Diagnosis_Pointer = driver.find_element(By.ID,
                                                                f"dnn_ctr724_SubmitProfessionalClaim3_ServiceDetailsDataList_SDDetailDiagPointer1CmnDropDownList_{num_factura}_Control_{num_factura}")
                        select = Select(Diagnosis_Pointer)
                        select.select_by_index(1)

                        Charge_Amount = driver.find_element(By.ID,
                                                            value=f"dnn_ctr724_SubmitProfessionalClaim3_ServiceDetailsDataList_SDDetailChargeAmountCmnTextBox_{num_factura}_Control_{num_factura}")
                        if ocurrencias==2:
                            driver.execute_script(f"arguments[0].value = '{suma_charges}';", Charge_Amount)
                        else:
                            driver.execute_script(f"arguments[0].value = '{Charge[ciclo]}';", Charge_Amount)
                        Units = driver.find_element(By.ID,
                                                    value=f"dnn_ctr724_SubmitProfessionalClaim3_ServiceDetailsDataList_SDDetailUnitsCmnTextBox_{num_factura}_Control_{num_factura}")
                        if ocurrencias == 2:
                            driver.execute_script(f"arguments[0].value = '{suma_unidades}';", Units)
                        else:
                            driver.execute_script(f"arguments[0].value = '{Unidades[ciclo]}';", Units)
                        Rendering_ID = driver.find_element(By.ID,
                                                           value=f"dnn_ctr724_SubmitProfessionalClaim3_ServiceDetailsDataList_SDDetailRenderingProviderIDCmnTextBox_{num_factura}_Control_{num_factura}")
                        Rendering_ID.send_keys(f"{provider_NPI}")

                        ID_Type = driver.find_element(By.ID,
                                                      f"dnn_ctr724_SubmitProfessionalClaim3_ServiceDetailsDataList_SDDetailRenderingProviderIDTypeCmnDropDownList_{num_factura}_Control_{num_factura}")
                        select = Select(ID_Type)
                        select.select_by_index(1)

                        add_button = driver.find_element(By.ID,
                                                         value=f"dnn_ctr724_SubmitProfessionalClaim3_ServiceDetailsDataList_SDAddCmnLinkButton_{num_factura}")
                        add_button.click()

                        num_factura+=1
                        ciclo += 1
                        pos += 1
                        guardar_progreso(cliente_i, provider_i, ciclo)

                        print(f"ciclo1: {ciclo}")
                        print(f"conteo {conteo}")
                        if ocurrencias == 2 and Billing_Codes[ciclo] == Billing_Codes[ciclo - 1]:
                            ciclo += 1
                            print(f"ciclo2: {ciclo}")
                            print(f"conteo1: {conteo}")
                            print(f"cantidad billing {len(Billing_Codes)}")
                        else:
                            if ciclo < conteo - 1:

                                if ocurrencias == 2 and Billing_Codes[ciclo] != Billing_Codes[ciclo + 1]:
                                    conteo -= 1

                                if ocurrencias == 2 and Billing_Codes[ciclo] == Billing_Codes[ciclo + 1]:
                                    ciclo += 1
                                    guardar_progreso(cliente_i, provider_i, ciclo)

                    mensaje = (
                        "✔️ FACTURACIÓN RELLENADA\n\n"
                        "La facturación fue rellenada correctamente.\n\n"
                        "Cuando estés listo, continúa y ve a Claim Prof."
                    )
                    mostrar_alerta(driver, mensaje)
                    WebDriverWait(driver, 999999).until_not(EC.alert_is_present())
                    guardar_progreso(cliente_i, provider_i + 1, 0)

                else:
                    print(f"ciclo {ciclo}")
                    fecha1=driver.find_element(By.ID,value=f"dnn_ctr724_SubmitProfessionalClaim3_ServiceDetailsDataList_SDDetailFromDateCmnDate_{pos}_Control_{pos}")
                    driver.execute_script(f"arguments[0].value = '{fechas[ciclo]}';", fecha1)

                    fecha2=driver.find_element(By.ID,value=f"dnn_ctr724_SubmitProfessionalClaim3_ServiceDetailsDataList_SDDetailToDateCmnDate_{pos}_Control_{pos}")
                    driver.execute_script(f"arguments[0].value = '{fechas[ciclo]}';", fecha2)

                    Place = driver.find_element(By.ID, f"dnn_ctr724_SubmitProfessionalClaim3_ServiceDetailsDataList_SDDetailPlaceOfServiceCmnDropDownList_{pos}_Control_{pos}")
                    select = Select(Place)
                    print(f"place {place_services[ciclo]}")
                    if place_services[ciclo]=="12":
                        select.select_by_index(12)
                    else:
                        select.select_by_index(3)
                    print(Billing_Codes[ciclo])

                    suma_charges = 0
                    suma_unidades=0
                    sumas=0
                    # Contar cuántas veces aparece la combinación fecha + billing code
                    ocurrencias = sum(
                        1 for j in range(len(fechas))
                        if fechas[j] == fechas[ciclo] and Billing_Codes[j] == Billing_Codes[ciclo]
                    )

                    # Solo sumar si ocurre exactamente 2 veces
                    if ocurrencias == 2:
                        for i in range(len(fechas)):
                            if fechas[i] == fechas[ciclo] and Billing_Codes[i] == Billing_Codes[ciclo]:
                                suma_charges += Charge[i]
                                suma_unidades += Unidades[i]
                                no_repetir = True


                    Procedure_Code=driver.find_element(By.ID,value=f"dnn_ctr724_SubmitProfessionalClaim3_ServiceDetailsDataList_SDDetailProcedureCodeCmnTextBox_{pos}_Control_{pos}")
                    Procedure_Code.send_keys(f"{Billing_Codes[ciclo]}")
                    time.sleep(1)

                    # Selecciona la primera sugerencia
                    Procedure_Code.send_keys(Keys.ARROW_DOWN)
                    Procedure_Code.send_keys(Keys.ENTER)


                    if str(Billing_Codes[ciclo])=="97153":
                        Modifier=driver.find_element(By.ID,value=f"dnn_ctr724_SubmitProfessionalClaim3_ServiceDetailsDataList_SDDetailModifier1CmnTextBox_{pos}_Control_{pos}")
                        Modifier.send_keys("UD-M/CAID CARE LEV 13 STATE DEF")


                    Diagnosis_Pointer = driver.find_element(By.ID, f"dnn_ctr724_SubmitProfessionalClaim3_ServiceDetailsDataList_SDDetailDiagPointer1CmnDropDownList_{pos}_Control_{pos}")
                    select = Select(Diagnosis_Pointer)
                    select.select_by_index(1)


                    Charge_Amount=driver.find_element(By.ID,value=f"dnn_ctr724_SubmitProfessionalClaim3_ServiceDetailsDataList_SDDetailChargeAmountCmnTextBox_{pos}_Control_{pos}")
                    if ocurrencias == 2:
                        driver.execute_script(f"arguments[0].value = '{suma_charges}';", Charge_Amount)
                    else:
                        driver.execute_script(f"arguments[0].value = '{Charge[ciclo]}';", Charge_Amount)
                    Units=driver.find_element(By.ID,value=f"dnn_ctr724_SubmitProfessionalClaim3_ServiceDetailsDataList_SDDetailUnitsCmnTextBox_{pos}_Control_{pos}")
                    if ocurrencias == 2:
                        driver.execute_script(f"arguments[0].value = '{suma_unidades}';", Units)
                    else:
                        driver.execute_script(f"arguments[0].value = '{Unidades[ciclo]}';", Units)

                    Rendering_ID=driver.find_element(By.ID,value=f"dnn_ctr724_SubmitProfessionalClaim3_ServiceDetailsDataList_SDDetailRenderingProviderIDCmnTextBox_{pos}_Control_{pos}")
                    Rendering_ID.send_keys(f"{provider_NPI}")


                    ID_Type = driver.find_element(By.ID, f"dnn_ctr724_SubmitProfessionalClaim3_ServiceDetailsDataList_SDDetailRenderingProviderIDTypeCmnDropDownList_{pos}_Control_{pos}")
                    select = Select(ID_Type)
                    select.select_by_index(1)

                    add_button=driver.find_element(By.ID,value=f"dnn_ctr724_SubmitProfessionalClaim3_ServiceDetailsDataList_SDAddCmnLinkButton_{pos}")
                    add_button.click()

                    ciclo+=1
                    pos+=1
                    guardar_progreso(cliente_i, provider_i, ciclo)
                    print(f"ciclo1: {ciclo}")
                    print(f"conteo {conteo}")
                    if ocurrencias == 2 and Billing_Codes[ciclo] == Billing_Codes[ciclo - 1]:
                        ciclo+=1
                        print(f"ciclo2: {ciclo}")
                        print(f"conteo1: {conteo}")
                        print(f"cantidad billing {len(Billing_Codes)}")
                    else:
                        if ciclo<conteo-1:

                            if ocurrencias == 2 and Billing_Codes[ciclo] != Billing_Codes[ciclo + 1] :
                                conteo -= 1

                            if ocurrencias == 2 and Billing_Codes[ciclo] == Billing_Codes[ciclo+1] :
                                ciclo+=1
                                guardar_progreso(cliente_i, provider_i, ciclo)

            mensaje = (
                "✔️ FACTURACIÓN RELLENADA\n\n"
                "La facturación fue rellenada correctamente.\n\n"
                "Cuando estés listo, continúa y ve a Claim Prof."
            )
            mostrar_alerta(driver, mensaje)
            WebDriverWait(driver, 999999).until_not(EC.alert_is_present())
            guardar_progreso(cliente_i, provider_i + 1, 0)


    WebDriverWait(driver, 9999).until(
                EC.presence_of_element_located((By.XPATH, "/html/body/form/div[3]/div/div[2]/div[3]/div[2]/table/tbody/tr/td/table/tbody/tr[2]/td[2]/div/div/div/div[1]/div/div[1]/div[2]/div/div[4]/div[3]/div[1]/div/div[2]/input"))
            )

    mensaje = (
        "✔️ PROCESO COMPLETADO\n\n"
        "Todos los clientes fueron facturados correctamente."
    )
    mostrar_alerta(driver, mensaje)
    WebDriverWait(driver, 999999).until_not(EC.alert_is_present())
    limpiar_progreso()
