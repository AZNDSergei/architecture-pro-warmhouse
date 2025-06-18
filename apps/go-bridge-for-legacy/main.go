package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"

	"github.com/google/uuid"
	"github.com/segmentio/kafka-go"
)

type Sensor struct {
	Id       int     `json:"id"`
	Name     string  `json:"name"`
	Type     string  `json:"type"`
	Location string  `json:"location"`
	Unit     string  `json:"unit"`
	Status   string  `json:"status"`
	Value    float64 `json:"value"`
}

type Device struct {
	ID              uuid.UUID  `json:"id"`
	Name            string     `json:"name"`
	Type            string     `json:"type"`
	Model           string     `json:"model"`
	FirmwareVersion string     `json:"firmware_version"`
	Status          string     `json:"status"`
	RoomID          *uuid.UUID `json:"room_id,omitempty"`
	HomeID          *uuid.UUID `json:"home_id,omitempty"`
	ActivationCode  *string    `json:"activation_code,omitempty"`
}

/* ---------- конфигурация ---------- */

const (
	targetURL          = "http://device-management:80/api/v2.0/sensors"
	topicLegacyAdd     = "legacyAddDevice"
	defaultBrokers     = "kafka:9092"
	consumerGroupID    = "legacy-device-gateway"
	defaultFirmwareVer = "legacy-1.0"
	defaultModel       = "legacy-sensor"
	listenTimeout      = 10 * time.Second
)

func main() {
	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	brokers := strings.Split(getEnv("KAFKA_BROKERS", defaultBrokers), ",")
	reader := kafka.NewReader(kafka.ReaderConfig{
		Brokers:         brokers,
		Topic:           topicLegacyAdd,
		GroupID:         consumerGroupID,
		MinBytes:        1e3,
		MaxBytes:        1e6,
		ReadLagInterval: -1,
	})
	defer reader.Close()

	httpClient := &http.Client{Timeout: listenTimeout}
	apiToken := getEnv("API_KEY", "")

	log.Printf("Waiting for messages on topic %q (brokers: %v)…", topicLegacyAdd, brokers)
	for {
		m, err := reader.ReadMessage(ctx)
		if err != nil {
			if ctx.Err() != nil {
				break
			}
			log.Printf("Kafka read error: %v", err)
			continue
		}

		var sensor Sensor
		if err := json.Unmarshal(m.Value, &sensor); err != nil {
			log.Printf("Cannot parse sensor JSON: %v (payload=%s)", err, string(m.Value))
			continue
		}

		device := mapSensorToDevice(sensor)
		if err := postDevice(ctx, httpClient, apiToken, device); err != nil {
			log.Printf("POST failed for sensor %d: %v", sensor.Id, err)
			continue
		}

		log.Printf("Sensor %d → device %s created", sensor.Id, device.ID)
	}
}

func mapSensorToDevice(s Sensor) Device {
	return Device{
		ID:              uuid.New(),
		Name:            s.Name,
		Type:            s.Type,
		Model:           firstNonEmpty(s.Unit, s.Location, defaultModel),
		FirmwareVersion: defaultFirmwareVer,
		Status:          firstNonEmpty(s.Status, "inactive"),
		// room_id, home_id, activation_code остаются nil
	}
}

func postDevice(ctx context.Context, c *http.Client, token string, d Device) error {
	body, _ := json.Marshal(d)

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, targetURL, bytes.NewReader(body))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	if token != "" {
		//req.Header.Set("Authorization", "Bearer "+token)
	}

	resp, err := c.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 300 {
		b, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("status %d: %s", resp.StatusCode, string(b))
	}
	return nil
}

func getEnv(key, fallback string) string {
	if v, ok := os.LookupEnv(key); ok {
		return v
	}
	return fallback
}

func firstNonEmpty(vals ...string) string {
	for _, v := range vals {
		if strings.TrimSpace(v) != "" {
			return v
		}
	}
	return ""
}
