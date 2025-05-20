from typing import Any
from core.broker import AMQPClient
from core.enums import EventStoreTypeEnum, RoutingTypeEnum


class BrokerManager:
    def __init__(self, event_store_key: EventStoreTypeEnum):
        self.event_store_key = event_store_key

    def publish_event(self, routing_key: RoutingTypeEnum, message: Any):
        with AMQPClient() as client:
            client.event_producer(
                event_store=self.event_store_key.value,
                routing_key=routing_key.value,
                message=message,
            )

    def consume_event(self, routing_key: RoutingTypeEnum, callback):
        with AMQPClient() as client:
            client.event_consumer(
                event_store=self.event_store_key.value,
                routing_key=routing_key.value,
                callback=callback,
            )
