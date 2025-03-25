import socket
import logging
import signal
import sys
sys.path.append('.')
from common.utils import store_bets
from common.msg_bet import receive_bet
from common.msg_bet import receive_integer
from common.utils import load_bets
from common.utils import has_won


class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self.running = True
        signal.signal(signal.SIGTERM, self.shutdown)
        self.clients_connected = []
        self.notified_agencies = set()
        self.winners = dict()

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
                #client = self.add_client(client_sock)
            except OSError:
                break


    def receive_bets(self, client_sock, total_bets):
        """Recibe apuestas del cliente y las almacena"""
        amount_batchs = receive_integer(client_sock)
        if amount_batchs is None:
            client_sock.sendall("ERROR\n".encode('utf-8'))
            logging.error(f'action: apuesta_recibida | result: fail | cantidad: {total_bets}')
            return -1
        

        for _ in range(amount_batchs):
            batch_size = receive_integer(client_sock)
            if batch_size is None:
                client_sock.sendall("ERROR\n".encode('utf-8'))
                logging.error(f'action: apuesta_recibida | result: fail | cantidad: {total_bets}')
                return -1

            bets = []
            for _ in range(batch_size):
                bet = receive_bet(client_sock)
                if bet is None:
                    client_sock.sendall("ERROR\n".encode('utf-8'))
                    logging.error(f'action: apuesta_recibida | result: fail | cantidad: {total_bets}')                        
                    return -1
                total_bets+=1
                bets.append(bet)

            store_bets(bets)

        return 0

    def sort_winners(self, client_sock):
        """Sortea los ganadores de las apuestas"""
        bets = load_bets()
        for bet in bets:
            if has_won(bet):
                if bet.agency not in self.winners:
                    self.winners[bet.agency] = []
                self.winners[bet.agency].append(bet.document)


    def __handle_client_connection(self, client_sock):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        total_bets = 0
        try:
            success = self.receive_bets(client_sock, total_bets)
            if success == -1:
                self.shutdown()
                return

            logging.info(f'action: apuesta_recibida | result: success | cantidad: {total_bets}')
            client_sock.sendall("OK\n".encode('utf-8'))
            
            msg = client_sock.recv(1024).decode('utf-8').strip()
            if msg == "END":
                self.notified_agencies.add(client_sock)
            
            if len(self.notified_agencies) == 5:
                self.sort_winners(client_sock)
                for agency, winners in self.winners.items():
                    # Esto esta mal. Deberia enviar solo los winnners de cada agencia, pero no se me ocurre como
                    client_sock.sendall(f"{agency}: {winners}\n".encode('utf-8'))
                    

        except OSError as e:
            logging.error(f'action: apuesta_recibida | result: fail | cantidad: {total_bets}')
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
