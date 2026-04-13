from cryptography.fernet import Fernet\


# Generar UNA sola clave (guárdala)
key = Fernet.generate_key()
print("GUARDA ESTA CLAVE:", key)

f = Fernet(key)

files_to_encrypt = {
    "avility-Usuarios.xlsx": "avility-Usuarios.dat",
    "medicaid-Usuarios.xlsx": "medicaid-Usuarios.dat",
    "usuarios_APP.xlsx": "usuarios_APP.dat"   # 👈 NUEVO
}

for input_file, output_file in files_to_encrypt.items():
    with open(input_file, "rb") as file:
        data = file.read()

    encrypted_data = f.encrypt(data)

    with open(output_file, "wb") as file:
        file.write(encrypted_data)

    print(f"{input_file} -> {output_file} cifrado")




































