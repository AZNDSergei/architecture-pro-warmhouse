package main

import (
	"context"
	"log"
	"os"
	"os/signal"
	"syscall"

	"go-bridge-for-legacy/consumer"
	"go-bridge-for-legacy/mapper"
	"go-bridge-for-legacy/sender"
)

func main() {
	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	brokers := getenv("KAFKA_BROKERS", consumer.DefaultBrokers)
	apiToken := getenv("API_KEY", "")

	log.Printf("Listening topic %q…", consumer.TopicLegacyAdd)
	err := consumer.Listen(ctx, brokers, func(msg []byte) {
		dev, err := mapper.SensorJSONToDevice(msg)
		if err != nil {
			log.Printf("parse error: %v", err)
			return
		}
		if err := sender.Send(ctx, dev, apiToken); err != nil {
			log.Printf("post error: %v", err)
		}
	})
	if err != nil && ctx.Err() == nil {
		log.Fatalf("consumer stopped: %v", err)
	}
}

func getenv(k, def string) string {
	if v, ok := os.LookupEnv(k); ok {
		return v
	}
	return def
}
