import socket
import logging
import signal
import sys
sys.path.append('.')
from common.utils import store_bets
from common.msg_bet import receive_bet
from common.msg_bet import receive_integer


class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)

        self.running = True
        signal.signal(signal.SIGTERM, self.shutdown)
        self.clients_connected = []

    def shutdown(self, signum, frame):
        """Maneja SIGTERM cerrando el socket correctamente"""
        self.running = False
        for client in self.clients_connected:
            addr = client.getpeername()
            logging.warning(f'clossing gracefully connection with client address: {addr[0]}')
            client.close()
        self._server_socket.close()
        logging.warning("action: shutdown | result: success")
        sys.exit(0)

    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """

        # the server
        while self.running:
            try:
                client_sock = self.__accept_new_connection()
                self.__handle_client_connection(client_sock)
            except OSError:
                break

    def __handle_client_connection(self, client_sock):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        try:
            total_bets = 0
            amount_batchs = receive_integer(client_sock)
            if amount_batchs is None:
                client_sock.sendall("ERROR\n".encode('utf-8'))
                return
            logging.info(f'action: amount_batchs | result: success | cantidad: {amount_batchs}')
            

            for _ in range(amount_batchs):
                batch_size = receive_integer(client_sock)
                if batch_size is None:
                    client_sock.sendall("ERROR\n".encode('utf-8'))
                    return

                bets = []
                for _ in range(batch_size):
                    bet = receive_bet(client_sock)
                    if bet is None:
                        client_sock.sendall("ERROR\n".encode('utf-8'))
                        return  # Si alguna apuesta falla, cancelamos todo
                    total_bets+=1
                    bets.append(bet)

                # Guardamos todas las apuestas en el archivo CSV
                store_bets(bets)
                


            logging.info(f'action: apuesta_recibida | result: success | cantidad: {total_bets}')
            client_sock.sendall("OK\n".encode('utf-8'))

        except OSError as e:
            logging.error("action: receive_message | result: fail | error: {e}")
        finally:
            client_sock.close()

    def __accept_new_connection(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """

        # Connection arrived
        logging.info('action: accept_connections | result: in_progress')
        c, addr = self._server_socket.accept()
        logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
        return c
