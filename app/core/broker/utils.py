from kombu import Queue, Exchange


class QueueExchangeUtil:
    @staticmethod
    def queue_exchange_formatting(event_store: str, routing_key: str) -> Queue:
        exchange = f"{event_store}_exchange"
        queue = f"{event_store}_queue"

        return Queue(queue, Exchange(exchange), routing_key=routing_key)
