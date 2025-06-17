import json
import asyncio
from typing import Optional

from aiokafka import AIOKafkaProducer

kafka_producer: Optional[AIOKafkaProducer] = None

async def get_kafka_producer() -> AIOKafkaProducer:
    global kafka_producer
    if kafka_producer is None:
        loop = asyncio.get_event_loop()
        kafka_producer = AIOKafkaProducer(
            bootstrap_servers="kafka:9092",
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        await kafka_producer.start()
    return kafka_producer

async def shutdown_kafka():
    global kafka_producer
    if kafka_producer:
        await kafka_producer.stop()
        kafka_producer = None
