import json
import redis
import os
from confluent_kafka import Consumer, KafkaError
from dotenv import load_dotenv
from src.pricing.cds import CDSAnalytics
from src.pricing.bond import BondAnalytics

load_dotenv()

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TOPIC_CDS = os.getenv("KAFKA_TOPIC_CDS", "market-data-cds")
TOPIC_BONDS = os.getenv("KAFKA_TOPIC_BONDS", "market-data-bonds")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

class RiskConsumer:
    def __init__(self):
        self.consumer = Consumer({
            "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
            "group.id": "risk-consumer-group-v2",
            "auto.offset.reset": "earliest"
        })
        self.consumer.subscribe([TOPIC_CDS, TOPIC_BONDS])
        self.redis = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

    def run(self):
        print(f"Starting RiskConsumer")
        try:
            while True:
                msg = self.consumer.poll(1.0)
                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        print(f"Kafka error: {msg.error()}")
                        break
                message = json.loads(msg.value().decode("utf-8"))
                instrument_id = message["instrument_id"]
                print(f"Received: {instrument_id}")

                try:
                    if message["product"] == "CDS":
                        risk = CDSAnalytics.calculate(message)
                    else:
                        risk = BondAnalytics.calculate(message)

                    self.redis.set(instrument_id, json.dumps(risk))
                    print(f"Cached: {instrument_id}")
                except Exception as e:
                    print(f"Pricing error for {instrument_id}: {e}")

        except KeyboardInterrupt:
            print("Shutting down consumer")
        finally:
            self.consumer.close()

if __name__ == "__main__":
    consumer = RiskConsumer()
    consumer.run()
