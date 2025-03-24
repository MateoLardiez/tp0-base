import socket
import struct

HOST = "127.0.0.1"  # Dirección del servidor
PORT = 12345  # Puerto donde corre el servidor

# Datos de la apuesta (Ejemplo)
nombre = "Mateo"
apellido = "Lardiez"
dni = "12345678"
nacimiento = "2002-08-15"
numero = "7574"

# Convertimos a bytes
nombre_b = nombre.encode('utf-8')
apellido_b = apellido.encode('utf-8')
dni_b = dni.encode('utf-8')
nacimiento_b = nacimiento.encode('utf-8')
numero_b = numero.encode('utf-8')

# Creamos el mensaje con las longitudes primero
header_format = "!5I"
header = struct.pack(header_format, len(nombre_b), len(apellido_b), len(dni_b), len(nacimiento_b), len(numero_b))

# Unimos el mensaje completo
payload = header + nombre_b + apellido_b + dni_b + nacimiento_b + numero_b

# Conectamos y enviamos los datos
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.connect((HOST, PORT))
    sock.sendall(payload)
    
    # Recibimos respuesta del servidor
    response = sock.recv(1024)
    print("Respuesta del servidor:", response.decode('utf-8'))
