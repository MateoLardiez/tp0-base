import struct
import logging
from utils import Bet


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
        header_data = client_sock.recv(header_size)

        if not header_data or len(header_data) != header_size:
            logging.error("Error al recibir las longitudes de los campos")
            return None

        agency_len, name_len, surname_len, dni_len, birthdate_len, number_len = struct.unpack(header_format, header_data)

        # Recibir los datos de acuerdo a las longitudes informadas
        total_data_length = agency_len + name_len + surname_len + dni_len + birthdate_len + number_len
        received_data = bytearray()

        while len(received_data) < total_data_length:
            chunk = client_sock.recv(total_data_length - len(received_data))
            if not chunk:
                logging.error("Conexión interrumpida antes de recibir todos los datos")
                return None
            received_data.extend(chunk)

        # Extraer los valores según los tamaños informados
        agency_number = received_data[:agency_len].decode('utf-8')
        name = received_data[:name_len].decode('utf-8')
        surname = received_data[name_len:name_len + surname_len].decode('utf-8')
        dni = received_data[name_len + surname_len:name_len + surname_len + dni_len].decode('utf-8')
        birthdate = received_data[name_len + surname_len + dni_len:name_len + surname_len + dni_len + birthdate_len].decode('utf-8')
        number = received_data[name_len + surname_len + dni_len + birthdate_len:].decode('utf-8')

        # Crear y devolver la apuesta
        return Bet(agency_number, name, surname, dni, birthdate, number)

    except (OSError, struct.error) as e:
        logging.error(f"Error al recibir la apuesta: {e}")
        return None
