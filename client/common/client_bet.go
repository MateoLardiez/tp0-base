package common

import (
	"bytes"
	"encoding/binary"
	"net"
)

type Bet struct {
	Agency    string
	FirstName string
	LastName  string
	Document  string
	Birthdate string
	Number    string
}

// SerializeBet convierte una apuesta en el protocolo definido
func SerializeBet(bet Bet) ([]byte, error) {
	fields := []string{bet.Agency, bet.FirstName, bet.LastName, bet.Document, bet.Birthdate, bet.Number}
	var buf bytes.Buffer

	// Escribir los tamaños de los campos
	for _, field := range fields {
		if err := binary.Write(&buf, binary.BigEndian, int32(len(field))); err != nil {
			return nil, err
		}
	}

	// Escribir los valores de los campos
	for _, field := range fields {
		if _, err := buf.WriteString(field); err != nil {
			return nil, err
		}
	}

	return buf.Bytes(), nil
}

func SendAll(conn net.Conn, data []byte) error {
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
