package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"time"

	"github.com/segmentio/kafka-go"
)

const (
	kafkaBroker = "kafka:9092"
	topic       = "sensorData"
)

var apiKey = getEnv("API_KEY", "my-secret-token")

type SensorType string

const (
	Temperature SensorType = "TEMPERATURE"
	Humidity    SensorType = "HUMIDITY"
	Pressure    SensorType = "PRESSURE"
)

type Sensor struct {
	ID       uint       `"primaryKey;autoIncrement"`
	Name     string     `"not null"`
	Type     SensorType `"type:VARCHAR(20);not null"`
	Location *string    `"type:VARCHAR(255)"`
	Value    *float64   `"type:FLOAT"`
	Unit     *string    `"type:VARCHAR(50)"`
	Status   *string    `"type:VARCHAR(50)"`
}

func main() {
	writer := kafka.NewWriter(kafka.WriterConfig{
		Brokers:  []string{kafkaBroker},
		Topic:    topic,
		Balancer: &kafka.LeastBytes{},
	})

	http.HandleFunc("/info", func(w http.ResponseWriter, r *http.Request) {

		log.Printf("Message is obtained")

		//if !authorize(r) {
		//	http.Error(w, "Unauthorized", http.StatusUnauthorized)
		//	return
		//}

		var msg Sensor
		if err := json.NewDecoder(r.Body).Decode(&msg); err != nil {
			http.Error(w, "Invalid JSON", http.StatusBadRequest)
			return
		}

		data, err := json.Marshal(msg)
		if err != nil {
			http.Error(w, "Failed to serialize", http.StatusInternalServerError)
			return
		}

		err = writer.WriteMessages(context.Background(),
			kafka.Message{
				Key:   []byte(fmt.Sprintf("key-%d", time.Now().UnixNano())),
				Value: data,
			})
		if err != nil {
			http.Error(w, "Failed to write to Kafka", http.StatusInternalServerError)
			log.Printf("Kafka error: %v", err)
			return
		}

		w.WriteHeader(http.StatusOK)
		w.Write([]byte("Message is obtained by timescale database. You can see records in compose logs"))
	})

	log.Println("Gateway with auth listening on :8080")
	log.Fatal(http.ListenAndServe(":8080", nil))
}

func getEnv(key, fallback string) string {
	if val, ok := os.LookupEnv(key); ok {
		return val
	}
	return fallback
}
