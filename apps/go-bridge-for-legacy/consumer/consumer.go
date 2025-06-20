package consumer

import (
	"context"
	"errors"
	"strings"
	"time"

	"github.com/segmentio/kafka-go"
)

type SensorMsgHandler func([]byte)

const (
	TopicLegacyAdd = "legacyAddDevice"
	DefaultBrokers = "kafka:9092"
)

func Listen(ctx context.Context, brokersCSV string, h SensorMsgHandler) error {
	brokers := strings.Split(brokersCSV, ",")

	// Ждем Kafka
	if err := waitForKafka(ctx, brokers, TopicLegacyAdd, 60*time.Second); err != nil {
		return err
	}

	r := kafka.NewReader(kafka.ReaderConfig{
		Brokers:        brokers,
		Topic:          TopicLegacyAdd,
		StartOffset:    kafka.FirstOffset,
		CommitInterval: time.Second,
	})
	defer r.Close()

	for {
		m, err := r.ReadMessage(ctx)
		if err != nil {
			return err
		}
		h(m.Value)
	}
}

func waitForKafka(ctx context.Context, brokers []string, topic string, timeout time.Duration) error {
	deadline := time.Now().Add(timeout)
	var lastErr error

	for time.Now().Before(deadline) {
		select {
		case <-ctx.Done():
			return ctx.Err()
		default:
			conn, err := kafka.DialLeader(ctx, "tcp", brokers[0], topic, 0)
			if err == nil {
				conn.Close()
				return nil
			}
			lastErr = err
			time.Sleep(2 * time.Second)
		}
	}
	return errors.New("Kafka is not ready: " + lastErr.Error())
}
