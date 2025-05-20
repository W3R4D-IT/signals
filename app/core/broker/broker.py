import json
import ssl
import contextlib
from collections.abc import Generator
from typing import Any
from kombu import Connection, Exchange, Queue

from core.config import settings


class BrokerClient:
    def __init__(self) -> None:
        """
        Initializes the AMQP client with the given RabbitMQ URL.
        """

    def init(self):
        """
        Initializes the AMQP connection and channel.
        """
        try:
            transport_options = None
            if settings.USE_SSL:
                transport_options = {
                    "ssl": {
                        "ssl_version": ssl.PROTOCOL_TLSv1_2,
                        "cert_reqs": ssl.CERT_REQUIRED,  # Require certificate validation
                    }
                }

            self.connection = Connection(
                hostname=settings.BROKER_HOSTNAME,
                port=settings.BROKER_PORT,
                userid=settings.BROKER_USERNAME,
                password=settings.BROKER_PASSWORD,
                virtual_host=settings.VIRTUAL_HOST,
                ssl=settings.USE_SSL,
                transport_options=transport_options,
            )

            self.channel = self.connection.channel()
        except Exception as e:
            print(f"Failed to connect to RabbitMQ: {e}")
            self.connection = None
            self.channel = None
        return self

    def event_producer(self, event_store: str, routing_key: str, message: Any) -> None:
        """
        Send event/message to a specific exchange/queue with routing-key.

        If an existing queue is bound to the given routing-key, the message will be stored
        to that queue otherwise the message will be lost.

        NOTE: The routing_key is mandatory so we can explicitly route the message/event
        to the right queue.
        """
        exchange = f"{event_store}_exchange"
        queue = f"{event_store}_queue"

        queue, exchange = self._set_up_exchange_queue(exchange, queue, routing_key)

        if isinstance(message, dict):
            message = json.dumps(message)

        with self.connection.Producer() as producer:
            producer.publish(
                message,
                exchange=exchange,
                routing_key=routing_key,
                serializer="json",
                content_type=settings.CONTENT_TYPE,
                content_encoding=settings.CONTENT_ENCODING,
                declare=[queue],
            )

    def event_consumer(self, event_store: str, routing_key: str, callback) -> None:
        """
        Consumes messages from a specific queue and processes them using the provided callback.
        """
        exchange = f"{event_store}_exchange"
        queue = f"{event_store}_queue"

        queue, exchange = self._set_up_exchange_queue(exchange, queue, routing_key)

        def _callback(body, message):
            callback(body)
            message.ack()

        with self.connection.Consumer(
            queue, callbacks=[_callback], accept=settings.ACCEPT_CONTENT.split()
        ) as _:
            print("Start consuming...")
            while True:
                self.connection.drain_events()

    def _set_up_exchange_queue(
        self, exchange: str, queue: str, routing_key: str
    ) -> tuple[Queue, Exchange]:
        exchange = Exchange(
            exchange,
            type=settings.EXCHANGE_TYPE,
            durable=settings.DURABLE,
        )
        queue = Queue(
            queue, exchange, routing_key=routing_key, durable=settings.DURABLE
        )
        return queue, exchange

    def close(self):
        """
        Closes the AMQP connection.
        """
        if self.connection:
            self.connection.close()


@contextlib.contextmanager
def AMQPClient() -> Generator[BrokerClient, None, None]:
    client = BrokerClient().init()
    try:
        yield client
    finally:
        client.close()
