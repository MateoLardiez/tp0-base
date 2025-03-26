import socket
import logging
import signal
import sys
import time
sys.path.append('.')
from common.utils import store_bets
from common.msg_bet import receive_bet
from common.msg_bet import receive_integer
from common.utils import load_bets
from common.utils import has_won
from common.msg_bet import send_winners


class Server:
    def __init__(self, port, listen_backlog, clients_amount):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self.running = True
        signal.signal(signal.SIGTERM, self.shutdown)
        self.clients_connected = {}
        self.clients_amount = clients_amount
        self.notified_agencies = 0
        self.winners = dict()
        self.lottery_run = False

    def shutdown(self, signum, frame):
        """Maneja SIGTERM cerrando el socket correctamente"""
        self.running = False
        for agency,client_socket in self.clients_connected.items():
            addr = client_socket.getpeername()
            logging.warning(f'clossing gracefully connection with client address: {addr[0]}, agency {agency}')
            client_socket.close()
        self._server_socket.close()
        logging.warning("action: shutdown | result: success")
        sys.exit(0)

    def add_client(self, client_sock):
        """Agrega un cliente a la lista de clientes conectados y obtiene nro de agencia"""
        agency_number = receive_integer(client_sock)
        if agency_number is None:
            client_sock.sendall("ERROR\n".encode('utf-8'))
            logging.error(f'action: receive_client | result: fail | ip: {client_sock.getpeername()[0]}')
            client_sock.close()
            return -1
        # Actualizo el client_sock, si es un cliente viejo o creo una clave nueva, si es un cliente nuevo
        if agency_number in self.clients_connected:
            logging.info(f"YA ESTABA CONECTADO EL CLIENTE {agency_number}")
        self.clients_connected[agency_number] = client_sock

        logging.info(f'action: receive_client | result: success | agency_number: {agency_number}')
        return 0

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
                succes = self.add_client(client_sock)
                if succes == -1:
                    logging.error(f'action: receive_client | result: fail | ip: {client_sock.getpeername()[0]}')
                    client_sock.close()
                    return
                self.__handle_client_connection(client_sock)
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

        return total_bets

    def sort_winners(self):
        """Sortea los ganadores de las apuestas"""
        bets = load_bets()
        for bet in bets:
            if has_won(bet):
                if bet.agency not in self.winners:
                    self.winners[bet.agency] = []
                self.winners[bet.agency].append(bet.document)
        self.lottery_run = True
        logging.info(f'action: sort_winners | result: success')


    def __handle_client_connection(self, client_sock):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """

        # Recibir el START o el END.
        # Si es END, chequea si ya se recibieron todas las apuestas
        '''
        if self.lottery_run:
            send_winners(client_sock, self.winners)
            return
            # Quizas es mejor enviar los winners solo cuando el cliente te lo pide. Evitar el for agency, winners ...
        '''
        # Si es start entra al try

        total_bets = 0
        try:
            #initial_msg = receive_integer(client_sock)
            #if initial_msg is None:
            #    client_sock.sendall("ERROR\n".encode('utf-8'))
            #    logging.error(f'action: receive_message | result: fail')
            #    return
            #if initial_msg == 1:
                #Enviar msg a agencia
            total_bets = self.receive_bets(client_sock, total_bets)
            if total_bets == -1:
                self.shutdown()
                return

            logging.info(f'action: apuesta_recibida | result: success | cantidad: {total_bets}')
            client_sock.sendall("OK\n".encode('utf-8'))
                        
            msg = client_sock.recv(1024).decode('utf-8').strip()
            if msg == "END":
                self.notified_agencies += 1
            
            time.sleep(1) # Para logs

            if (not self.lottery_run) and (self.notified_agencies == self.clients_amount):
                time.sleep(1) # Para logs
                logging.info(f"EMPEZANDO A SORTEAR con {self.notified_agencies} agencias y {self.clients_amount} clientes conectados")
                self.sort_winners()
                actual_client_sock = client_sock
                for agency, winners_of_agency in self.winners.items():
                    actual_client_sock = self.clients_connected[agency]
                    send_winners(actual_client_sock, winners_of_agency)
                    
                for agency, client_sock in self.clients_connected.items():
                    client_sock.close()
                    logging.info(f"action: cerrando_conexion | result: success | agency: {agency}")

        except OSError as e:
            logging.error(f'action: apuesta_recibida | result: fail | cantidad: {total_bets}')
            logging.error("action: receive_message | result: fail | error: {e}")
        
        # Para los tests
        #finally:
        #    client_sock.close()

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
