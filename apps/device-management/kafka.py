import json
from typing import AsyncGenerator, Optional

from aiokafka import AIOKafkaProducer

__all__ = ["get_kafka_producer", "shutdown_kafka"]

BOOTSTRAP_SERVERS = "kafka:9092"


def _json_serializer(obj) -> bytes:
    return json.dumps(obj, default=str).encode()
_kafka_producer: Optional[AIOKafkaProducer] = None


async def get_kafka_producer() -> AsyncGenerator[AIOKafkaProducer, None]:

    global _kafka_producer

    if _kafka_producer is None:
        _kafka_producer = AIOKafkaProducer(
            bootstrap_servers=BOOTSTRAP_SERVERS,
            key_serializer=str.encode,
            value_serializer=_json_serializer,
        )
        await _kafka_producer.start()

    try:
        yield _kafka_producer
    finally:
       
        pass



async def shutdown_kafka() -> None:
    global _kafka_producer
    if _kafka_producer is not None:
        await _kafka_producer.stop()
        _kafka_producer = None
