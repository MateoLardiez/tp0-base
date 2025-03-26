import struct
import logging
from common.utils import Bet



def recv_all(sock, size):
    """ Intenta recibir exactamente 'size' bytes del socket, manejando short reads. """
    data = bytearray()
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:  # Si no recibe mas datos, hay un error en la conexion
            return None
        data.extend(chunk)
    return data

def send_all(sock, data):
    """Envía todos los datos al socket, manejando short writes."""
    total_sent = 0
    while total_sent < len(data):
        sent = sock.send(data[total_sent:])
        if sent == 0:
            raise RuntimeError("Conexión cerrada inesperadamente")
        total_sent += sent


def receive_bet(client_sock):
    """
    Recibe y parsea una apuesta desde un socket de cliente.

    Args:
        client_sock: socket del cliente.

    Returns:
        Una instancia de Bet si la recepción es exitosa, None en caso de error.
    """
    try:
        # Recibir los primeros 6 enteros (cada uno de 4 bytes)
        header_format = "!6I"  # 6 enteros sin signo en formato big-endian
        header_size = struct.calcsize(header_format)
        header_data = recv_all(client_sock, header_size)

        if not header_data or len(header_data) != header_size:
            logging.error("Error al recibir las longitudes de los campos")
            return None

        agency_len, name_len, surname_len, dni_len, birthdate_len, number_len = struct.unpack(header_format, header_data)

        # Recibir los datos de acuerdo a las longitudes informadas
        total_data_length = agency_len + name_len + surname_len + dni_len + birthdate_len + number_len

        received_data = recv_all(client_sock, total_data_length)

        # Extraer los valores según los tamaños informados
        agency_number = received_data[:agency_len].decode('utf-8')
        name = received_data[agency_len:agency_len + name_len].decode('utf-8')
        surname = received_data[agency_len + name_len:name_len + surname_len].decode('utf-8')
        dni = received_data[agency_len + name_len + surname_len:agency_len + name_len + surname_len + dni_len].decode('utf-8')
        birthdate = received_data[agency_len + name_len + surname_len + dni_len:agency_len + name_len + surname_len + dni_len + birthdate_len].decode('utf-8')
        number = received_data[agency_len + name_len + surname_len + dni_len + birthdate_len:].decode('utf-8')

        # Crear y devolver la apuesta
        return Bet(agency_number, name, surname, dni, birthdate, number)

    except (OSError, struct.error) as e:
        logging.error(f"Error al recibir la apuesta: {e}")
        return None

def receive_integer(client_sock) -> int:
    """
    Recibe un entero de 4 bytes desde un socket de cliente.

    Args:
        client_sock: socket del cliente.

    Returns:
        El entero recibido si la recepción es exitosa, None en caso de error.
    """
    try:
        data = recv_all(client_sock, 4)
        if not data or len(data) != 4:
            logging.error("Error al recibir el entero")
            return None
        return struct.unpack("!I", data)[0]
    except (OSError, struct.error) as e:
        logging.error(f"Error al recibir el entero: {e}")
        return None
    
def send_winners(client_sock, winners):
    """
    Envía la lista de DNIs de los ganadores a través del socket.

    Args:
        client_sock: socket del cliente
        winners: lista de DNIs de los ganadores (como strings)
    """
    # Convertir la cantidad de ganadores a 4 bytes (big-endian)
    num_winners = len(winners)
    data = struct.pack("!I", num_winners)

    # Convertir cada ganador a bytes y agregar su tamaño
    winners_bytes = [w.encode('utf-8') for w in winners]
    for w in winners_bytes:
        data += struct.pack("!I", len(w))  # Tamaño del DNI en 4 bytes
    for w in winners_bytes:
        data += w  # Agregar el DNI en bytes

    # Enviar toda la información usando send_all
    send_all(client_sock, data)
    logging.info(f'action: ganadores_enviados | result: success | cantidad: {num_winners}')