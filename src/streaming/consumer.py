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
            "group.id": "risk-consumer-group",
            "auto.offset.reset": "earliest"
        })
        self.consumer.subscribe([TOPIC_CDS, TOPIC_BONDS])
        self.redis = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

    def _price_cds(self, message: dict) -> dict:
        # TODO: cache CDSAnalytics instances by instrument_id to avoid reinstantiation on every tick
        analytics = CDSAnalytics(
            instrument_id=message["instrument_id"],
            maturity_date=message["maturity_date"],
            coupon_bps=message["coupon_bps"],
            notional=message["notional"]
        )
        spread_bps = message["spread_bps"]
        rate = message["rate"]
        end_date = message["maturity_date"]
    
        return {
            "instrument_id": message["instrument_id"],
            "product": "CDS",
            "upfront": analytics.calc_upfront(spread_bps, end_date, rate),
            "cs01": analytics.calc_cs01(spread_bps, end_date, rate),
            "jump_to_default": analytics.calc_jump_to_default(spread_bps, end_date, rate),
            "carry": analytics.calc_carry(spread_bps),
            "ir01": analytics.calc_ir01(spread_bps, end_date, rate)
        }
    
    def _price_bond(self, message: dict) -> dict:
            # TODO: cache BondAnalytics instances by instrument_id to avoid reinstantiation on every tick
            analytics = BondAnalytics(
                instrument_id=message["instrument_id"],
                start_date=message["start_date"],
                maturity_date=message["maturity_date"],
                coupon_bps=message["coupon_bps"],
                notional=message["notional"],
                payment_frequency=message["payment_frequency"],
                day_count_convention=message["day_count_convention"]                              
            )

            rate = message["rate"]
            market_price=analytics.calc_dirty_price(rate)
            
            return {
                "instrument_id": message["instrument_id"],
                "product": "BOND",
                "dirty_price": analytics.calc_dirty_price(rate),
                "accrued_interest": analytics.calc_accrued_interest(),
                "clean_price": analytics.calc_clean_price(rate),
                "ytm": analytics.calc_ytm(market_price),
                "dv01": analytics.calc_dv01(rate),
                "duration": analytics.calc_duration(rate),
                "convexity": analytics.calc_convexity(rate),
                "z_spread": analytics.calc_z_spread(rate , market_price),
                "carry": analytics.calc_carry()
            }

    def run(self):
        print(f"Starting RiskConsumer, listening to {TOPIC_CDS} and {TOPIC_BONDS}")
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
                if msg.topic() == TOPIC_CDS:
                    result = self._price_cds(message)
                else:
                    result = self._price_bond(message)
                self.redis.setex(
                    name=result["instrument_id"],
                    time=60,
                    value=json.dumps(result)
                )
        except KeyboardInterrupt:
            print("Shutting down consumer")
        finally:
            self.consumer.close()

    if __name__ == "__main__":
        consumer = RiskConsumer()
        consumer.run()

    