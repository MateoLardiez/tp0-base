import socket
import logging
import signal
import sys
import time
sys.path.append('.')
from common.utils import store_bets, load_bets, has_won
from common.msg_bet import receive_bet, receive_integer, send_winners

from multiprocessing import Process, Barrier, Manager, Lock, Value



class Server:
    def __init__(self, port, listen_backlog, clients_amount):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self.running = True
        signal.signal(signal.SIGTERM, self.shutdown)
        self.clients_amount = clients_amount

        manager = Manager()

        self.clients_connected = dict() #No creo q haga falta. Se usa en el add y desp en handle_bets
        self.notified_agencies = Value('i', 0)
        #self.winners = dict()
        self.winners = manager.dict()
        self.lottery_run = Value('b', False)
        self.bets_file_lock = Lock()
        self.variables_lock = Lock()
        self.start_lottery_barrier = Barrier(clients_amount)

    def shutdown(self, signum, frame):
        """Maneja SIGTERM cerrando el socket correctamente"""
        self.running = False
        for agency,client_socket in self.clients_connected.items():
            addr = client_socket.getpeername()
            logging.warning(f'clossing gracefully connection with client address: {addr[0]}, agency {agency}')
            client_socket.close()

        for process in self.processes:
            process.terminate()
            process.join()
        
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
        self.winners[agency_number] = []

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
        processes = []  
        while self.running:
            try:
                client_sock = self.__accept_new_connection()
                succes = self.add_client(client_sock)
                if succes == -1:
                    logging.error(f'action: receive_client | result: fail | ip: {client_sock.getpeername()[0]}')
                    client_sock.close()
                    return
                process = Process(target=self.__handle_client_connection, args=(client_sock,))
                processes.append(process)
                process.start()

            except OSError:
                break

        # Wait for all processes to finish
        for process in processes:
            try:
                process.join()
            except:
                logging.error(f"action: closing_processes | result: fail | process_name: {process.name} | process_id: {process.pid}")
        
        logging.info("action: server_loop_ended | result: success")
        


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

            # Lock para evitar condiciones de carrera al escribir en el archivo
            with self.bets_file_lock:
                store_bets(bets)

        return total_bets

    def sort_winners(self):
        """Sortea los ganadores de las apuestas"""
        bets = load_bets()
        for bet in bets:
            if has_won(bet):
                # Obtener la lista actual de ganadores para la agencia
                current_winners = self.winners.get(bet.agency, [])
                
                # Agregar el nuevo ganador a la lista
                current_winners.append(bet.document)
                
                # Reasignar la lista actualizada al diccionario compartido
                self.winners[bet.agency] = current_winners
        self.lottery_run.value = True
        logging.info(f'action: sort_winners | result: success')

    def handle_bets(self, client_sock):
        """Maneja el envio de los ganadores a la agencia"""
        logging.info(f'action: handle_bets | result: in_progress')
        with self.variables_lock:
            if (not self.lottery_run.value) and (self.notified_agencies.value == self.clients_amount):
                logging.info(f'action: handle_bets | result: in_progress | notified_agencies: {self.notified_agencies.value} | clients_amount: {self.clients_amount}')
                #time.sleep(1) # Para logs
                self.sort_winners()
                #actual_client_sock = client_sock
                #for agency, winners_of_agency in self.winners.items():
                #    actual_client_sock = self.clients_connected[agency]
                #    send_winners(actual_client_sock, winners_of_agency)
            
                #for agency, client_sock in self.clients_connected.items():
                #    client_sock.close()
                #    logging.info(f"action: cerrando_conexion | result: success | agency: {agency}")


    def __handle_client_connection(self, client_sock):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        total_bets = 0
        try:
            total_bets = self.receive_bets(client_sock, total_bets)
            if total_bets == -1:
                self.shutdown()
                return

            logging.info(f'action: apuesta_recibida | result: success | cantidad: {total_bets}')
            client_sock.sendall("OK\n".encode('utf-8'))
                        
            msg = client_sock.recv(1024).decode('utf-8').strip()
            if msg == "END":
                with self.variables_lock:
                    self.notified_agencies.value += 1

            agency_id = next((clave for clave, valor in self.clients_connected.items() if valor == client_sock), None)
            logging.info(f"esperando barrera | agency_num: {agency_id} | notified_agencies: {self.notified_agencies.value} | clients_amount: {self.clients_amount}")
            self.start_lottery_barrier.wait()  # Espera a que todos los clientes envíen "END"
            logging.info(f'action: sorteo | result: success')

            # time.sleep(1) # Para logs

            self.handle_bets(client_sock)

            with self.variables_lock:
                send_winners(client_sock, self.winners[agency_id])

        except OSError as e:
            logging.error(f'action: apuesta_recibida | result: fail | cantidad: {total_bets}')
            logging.error("action: receive_message | result: fail | error: {e}")
        
        finally:
            client_sock.close()
            logging.info(f"action: cerrando_conexion | result: success | agency: {agency_id}")

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
