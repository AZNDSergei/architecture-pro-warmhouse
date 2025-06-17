#!/bin/sh

RAW_BOOTSTRAP="${KAFKA_BOOTSTRAP_SERVERS:-kafka:9092}"

# если переменная в виде host:port — отделяем
KAFKA_HOST=$(echo "$RAW_BOOTSTRAP" | cut -d: -f1)
KAFKA_PORT=$(echo "$RAW_BOOTSTRAP" | cut -d: -f2)

# если порт не указан — по умолчанию 9092
[ -z "$KAFKA_PORT" ] && KAFKA_PORT=9092

echo "Waiting for Kafka to be available at $KAFKA_HOST:$KAFKA_PORT..."

while ! nc -z "$KAFKA_HOST" "$KAFKA_PORT"; do
  echo "Kafka not ready yet..."
  sleep 2
done

echo "Kafka is available. Executing command:"
exec "$@"
