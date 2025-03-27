package common

import (
	"bytes"
	"encoding/binary"
	"encoding/csv"
	"fmt"
	"io"
	"net"
	"os"
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

// ReadBetsFromCSV lee un archivo CSV y devuelve una lista de apuestas
func ReadBetsFromCSV(filename string, agencyID string) ([]Bet, error) {
	file, err := os.Open(filename)
	if err != nil {
		return nil, fmt.Errorf("error abriendo el archivo CSV: %w", err)
	}
	defer file.Close()

	reader := csv.NewReader(file)
	records, err := reader.ReadAll()
	if err != nil {
		return nil, fmt.Errorf("error leyendo el archivo CSV: %w", err)
	}

	var bets []Bet
	for _, record := range records {
		if len(record) < 5 {
			continue // Saltar líneas inválidas
		}
		bets = append(bets, Bet{
			Agency:    agencyID,
			FirstName: record[0],
			LastName:  record[1],
			Document:  record[2],
			Birthdate: record[3],
			Number:    record[4],
		})
	}

	return bets, nil
}

// SplitBetsIntoBatches divide una lista de apuestas en batches de tamaño máximo `batchSize` o de 8192 bytes(kb)
func SplitBetsIntoBatches(bets []Bet, batchSize int) [][]Bet {
	var batches [][]Bet
	var currentBatch []Bet
	var currentSize int

	for _, bet := range bets {
		serializedBet, err := SerializeBet(bet)
		if err != nil {
			log.Errorf("action: serialize_bet | result: fail | error: %v", err)
			continue
		}

		betSize := len(serializedBet)

		// Si agregar esta apuesta supera los 8188 bytes(+4 bytes para cant_bets), cerramos el batch actual
		// y empezamos uno nuevo
		if currentSize+betSize > 8188 || len(currentBatch) >= batchSize {
			batches = append(batches, currentBatch)
			currentBatch = []Bet{}
			currentSize = 0
		}

		currentBatch = append(currentBatch, bet)
		currentSize += betSize
	}

	// Agregar el último batch si no está vacío
	if len(currentBatch) > 0 {
		batches = append(batches, currentBatch)
	}

	return batches
}

func SerializeBatch(bets []Bet) ([]byte, error) {
	var buf bytes.Buffer
	// Escribir la cantidad de apuestas como un entero al inicio
	if err := binary.Write(&buf, binary.BigEndian, int32(len(bets))); err != nil {
		return nil, err
	}
	for _, bet := range bets {
		serializedBet, err := SerializeBet(bet)
		if err != nil {
			return nil, err
		}
		if _, err := buf.Write(serializedBet); err != nil {
			return nil, err
		}
	}
	return buf.Bytes(), nil
}

func ReceiveWinners(conn net.Conn) ([]string, error) {
	var numWinners uint32

	// Leer el número de ganadores (4 bytes)
	err := binary.Read(conn, binary.BigEndian, &numWinners)
	if err != nil {
		return nil, fmt.Errorf("error reading number of winners: %w", err)
	}

	winners := make([]string, numWinners)
	if numWinners == 0 {
		return winners, nil
	}

	// Leer el tamaño de cada DNI (4 bytes cada uno)
	dniSizes := make([]uint32, numWinners)
	for i := uint32(0); i < numWinners; i++ {
		err := binary.Read(conn, binary.BigEndian, &dniSizes[i])
		if err != nil {
			return nil, fmt.Errorf("error reading DNI size: %w", err)
		}
	}

	// Leer los DNIs
	for i := uint32(0); i < numWinners; i++ {
		dniBytes := make([]byte, dniSizes[i])
		_, err := io.ReadFull(conn, dniBytes)
		if err != nil {
			return nil, fmt.Errorf("error reading DNI: %w", err)
		}
		winners[i] = string(dniBytes)
	}

	return winners, nil
}
