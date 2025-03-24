package common

import (
	"bufio"
	"net"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"

	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("log")

// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID            string
	ServerAddress string
	LoopAmount    int
	LoopPeriod    time.Duration
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
	nombre := os.Getenv("CLI_NOMBRE")
	apellido := os.Getenv("CLI_APELLIDO")
	documento := os.Getenv("CLI_DOCUMENTO")
	nacimiento := os.Getenv("CLI_NACIMIENTO")
	numero := os.Getenv("CLI_NUMERO")

	var bet = Bet{
		Agency:    c.config.ID,
		FirstName: nombre,
		LastName:  apellido,
		Document:  documento,
		Birthdate: nacimiento,
		Number:    numero,
	}
	log.Debugf("action: bet created | result: success | bet: %v", bet)

	return bet, nil
}

// handleShutdown maneja SIGTERM y cierra la conexión correctamente
func (c *Client) handleShutdown() {
	<-c.stop // Bloquea hasta que reciba SIGTERM o SIGINT
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

// StartClientLoop Send messages to the client until some time threshold is met
func (c *Client) StartClientLoop() {
	// There is an autoincremental msgID to identify every message sent
	// Messages if the message amount threshold has not been surpassed
	bet, err := c.GetBetData()
	c.createClientSocket()

	if err != nil {
		log.Errorf("action: get_bet_data | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
		return
	}

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
	_, err_send := c.conn.Write(data)
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

	/*
		// TODO: Modify the send to avoid short-write
		fmt.Fprintf(
			c.conn,
			"[CLIENT %v] Message N°%v\n",
			c.config.ID,
			msgID,
		)
		msg, err := bufio.NewReader(c.conn).ReadString('\n')
		c.conn.Close()

		if err != nil {
			log.Errorf("action: receive_message | result: fail | client_id: %v | error: %v",
				c.config.ID,
				err,
			)
			return
		}
	*/

	log.Infof("action: receive_message | result: success | client_id: %v | msg: %v",
		c.config.ID,
	)

	// Wait a time between sending one message and the next one
	time.Sleep(c.config.LoopPeriod)

	log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
}
