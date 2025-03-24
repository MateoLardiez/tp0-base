package common

import (
	"bufio"
	"fmt"
	"net"
	"os"
	"os/signal"
	"regexp"
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

func sendAll(conn net.Conn, data []byte) error {
	totalSent := 0
	for totalSent < len(data) {
		n, err := conn.Write(data[totalSent:])
		if err != nil {
			return err
		}
		totalSent += n
	}
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
	err_send := sendAll(c.conn, data)
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

	log.Infof("action: receive_message | result: success | client_id: %v",
		c.config.ID,
	)

	// Wait a time between sending one message and the next one
	time.Sleep(c.config.LoopPeriod)

	log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
}
