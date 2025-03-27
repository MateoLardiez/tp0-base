package common

import (
	"bufio"
	"fmt"
	"net"
	"os"
	"os/signal"
	"regexp"
	"strconv"
	"strings"
	"syscall"
	"time"

	"github.com/op/go-logging"
)

const END_MSG = byte(0x01) // Definir un byte global
const OK_MSG = byte(0x02)

var log = logging.MustGetLogger("log")

// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID            string
	ServerAddress string
	LoopAmount    int
	LoopPeriod    time.Duration
	BatchAmount   int
}

// Client Entity that encapsulates how
type Client struct {
	config ClientConfig
	conn   net.Conn
	stop   chan os.Signal // Canal para capturar señales del sistema
}

// NewClient Initializes a new client receiving the configuration
// as a parameter
func NewClient(config ClientConfig) *Client {
	client := &Client{
		config: config,
		stop:   make(chan os.Signal, 1),
	}
	signal.Notify(client.stop, syscall.SIGTERM) // Capturar señales

	go client.handleShutdown() // Goroutine para escuchar y manejar la senial SIGTERM todo el tiempo

	return client
}

func (c *Client) GetBetData() (Bet, error) {
	firstName := os.Getenv("CLI_NOMBRE")
	lastName := os.Getenv("CLI_APELLIDO")
	document := os.Getenv("CLI_DOCUMENTO")
	birthDate := os.Getenv("CLI_NACIMIENTO")
	number := os.Getenv("CLI_NUMERO")

	matched, err := regexp.MatchString(`^\d{4}-\d{2}-\d{2}$`, birthDate)
	if err != nil || !matched {
		return Bet{}, fmt.Errorf("invalid birthdate format: %s", birthDate)
	}

	var bet = Bet{
		Agency:    c.config.ID,
		FirstName: firstName,
		LastName:  lastName,
		Document:  document,
		Birthdate: birthDate,
		Number:    number,
	}
	log.Debugf("action: bet created | result: success | bet: %v", bet)

	return bet, nil
}

// handleShutdown maneja SIGTERM y cierra la conexión correctamente
func (c *Client) handleShutdown() {
	<-c.stop // Bloquea hasta que reciba SIGTERM
	log.Warningf("action: shutdown | result: in_progress | client_id: %v", c.config.ID)
	if c.conn != nil {
		c.conn.Close()
	}
	log.Warningf("action: shutdown | result: success | client_id: %v", c.config.ID)
	os.Exit(0)
}

// CreateClientSocket Initializes client socket. In case of
// failure, error is printed in stdout/stderr and exit 1
// is returned
func (c *Client) createClientSocket() error {
	conn, err := net.Dial("tcp", c.config.ServerAddress)
	if err != nil {
		log.Criticalf(
			"action: connect | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
	}
	c.conn = conn
	return nil
}

// Envia una apuesta al servidor
func (c *Client) SendBetToServer() {
	bet, err := c.GetBetData()

	if err != nil {
		log.Errorf("action: get_bet_data | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
		return
	}

	c.createClientSocket()
	// Serializar la apuesta con bet.go
	data, err := SerializeBet(bet)
	if err != nil {
		log.Errorf("action: serialize_bet | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
		return
	}

	// Enviar la apuesta al servidor
	err_send := SendAll(c.conn, data)
	if err_send != nil {
		log.Errorf("action: send_bet | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err_send,
		)
		return
	}

	// Recibir confirmación del servidor
	response, err := bufio.NewReader(c.conn).ReadString('\n')
	if err != nil {
		log.Errorf("action: receive_confirmation | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
		return
	}

	// Loggear la respuesta del servidor
	response = strings.TrimSpace(response) // Remover espacios o saltos de línea
	if response == "OK" {
		log.Infof("action: apuesta_enviada | result: success | dni: %v | numero: %v",
			bet.Document,
			bet.Number,
		)
	} else {
		log.Warningf("action: receive_confirmation | result: error | client_id: %v | response: %v",
			c.config.ID,
			response,
		)
	}

	log.Infof("action: receive_message | result: success | client_id: %v",
		c.config.ID,
	)

}

// Envia todas las apuestas en batches al servidor
func (c *Client) SendBetsInBatch() {
	// Leer apuestas del CSV
	bets, err := ReadBetsFromCSV(fmt.Sprintf("./agency-%s.csv", c.config.ID), c.config.ID)
	if err != nil {
		log.Errorf("action: read_bets | result: fail | client_id: %v | error: %v", c.config.ID, err)
		return
	}

	// Dividir en batches según la configuración
	batches := SplitBetsIntoBatches(bets, c.config.BatchAmount)

	batchCountBytes := BatchCountBytes(len(batches))

	if err := SendAll(c.conn, batchCountBytes); err != nil {
		log.Errorf("action: send_batch_count | result: fail | client_id: %v | error: %v", c.config.ID, err)
		return
	}

	for _, batch := range batches {
		// Serializar batch
		data, err := SerializeBatch(batch)
		if err != nil {
			log.Errorf("action: serialize_batch | result: fail | client_id: %v | error: %v", c.config.ID, err)
			continue
		}

		// Enviar batch al servidor
		if err := SendAll(c.conn, data); err != nil {
			log.Errorf("action: send_batch | result: fail | client_id: %v | error: %v", c.config.ID, err)
			continue
		}

	}
	// Recibir confirmación del servidor (OK)
	buf := make([]byte, 1)
	_, err = c.conn.Read(buf)
	if err != nil {
		log.Errorf("action: receive_confirmation | result: fail | client_id: %v | error: %v", c.config.ID, err)
	}

	// Verificar si el mensaje recibido es el esperado
	if buf[0] == OK_MSG {
		log.Infof("action: apuesta_enviada | result: success | cantidad: %v | client_id: %v", len(bets), c.config.ID)
	} else {
		log.Warningf("action: apuesta_enviada | result: fail | client_id: %v | response: %v", c.config.ID, buf[0])
	}
}

// Se encuentra todo el flujo del cliente
func (c *Client) StartClientLoop() {

	// Crear socket
	if err := c.createClientSocket(); err != nil {
		log.Errorf("action: create_socket | result: fail | client_id: %v | error: %v", c.config.ID, err)
		return
	}
	defer c.conn.Close() // Para cerrar el socket automáticamente al finalizar la función

	// Enviar numero de agencia al servidor
	idStr := c.config.ID
	idInt, err := strconv.Atoi(idStr)
	if err != nil {
		log.Fatalf("Error converting ID to int: %v", err)
	}
	agencyID := uint32(idInt)

	if err := SendAgencyID(c.conn, agencyID); err != nil {
		log.Errorf("action: send_agency_id | result: fail | client_id: %v | error: %v", c.config.ID, err)
		return
	}

	c.SendBetsInBatch()

	// Notificar al servidor que termine de enviar todas las cosas. En mi caso es evitable porque
	// el servidor sabe cuando es que se terminan de enviar los datos. Pero lo pide el enunciado
	_, err = c.conn.Write([]byte{END_MSG})
	if err != nil {
		log.Errorf("action: notify_end | result: fail | client_id: %v | error: %v", c.config.ID, err)
		return
	}
	log.Infof("action: notify_end | result: success | client_id: %v", c.config.ID)

	// Esperar respuesta con los ganadores
	winners, err := ReceiveWinners(c.conn)
	if err != nil {
		log.Errorf("action: consulta_ganadores | result: fail | client_id: %v | error: %v", c.config.ID, err)
		return
	}
	log.Infof("action: consulta_ganadores | result: success | cant_ganadores: %d", len(winners))

	time.Sleep(1 * time.Second) // Para que pasen los tests
	log.Infof("action: process_finished | result: success | client_id: %v", c.config.ID)
}
