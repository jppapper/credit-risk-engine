"""
Market Data Simulator
_____________________

Generates realistic spread and rate data for 50k instruments 
and streams to Kafka topics partitioned by product type.
"""
import json
import random
import time
import numpy as np
from confluent_kafka import Producer
from dotenv import load_dotenv
import os
import datetime

load_dotenv()

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TOPIC_CDS = os.getenv("KAFKA_TOPIC_CDS", "market-data-cds")
TOPIC_BONDS = os.getenv("KAFKA_TOPIC_BONDS", "market-data-bonds")
NUM_INSTRUMENTS = int(os.getenv("NUM_INSTRUMENTS", 50000))

class MarketDataSimulator:
    def __init__(self, num_instruments: int):
        self.num_instruments = num_instruments
        self.producer = Producer({"bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS})
        self.instruments = []

    def build_universe(self):
        for i in range (self.num_instruments):
            product = "CDS" if i % 2 == 0 else "BOND"
            self.instruments.append({
                "instrument_id": f"{product}-{i:05d}",
                "product": product,
                "spread_bps": random.uniform(50, 500),
                "rate": random.uniform(0.03, 0.07),
                "maturity_date": (datetime.date.today() + datetime.timedelta(days=random.choice([365, 730, 1095, 1825, 2555, 3650]))).isoformat(),
                "start_date": datetime.date.today().isoformat(),
                "coupon_bps": random.choice([100, 500]) if product == "CDS" else random.uniform(200, 800),
                "payment_frequency": 2,
                "day_count_convention": "30/360",
                "notional": random.choice([1_000_000, 5_000_000, 10_000_000, 25_000_000])
                })
        return self.instruments
    
    def simulate_market_movement(self, instrument: dict) -> dict:
        rate_move = np.random.normal(0, 0.001)
        spread_move = np.random.normal(0, 2)

        instrument["spread_bps"] = max(1, instrument["spread_bps"] + spread_move)
        instrument["rate"] = max(0.001, instrument['rate'] + rate_move)
        instrument["timestamp"] = time.time()
        return instrument
    
    def delivery_report(self, err, msg):
        if err:
            print(f"Delivery failed: {err}")
    
    def run_simulator(self, ticks: int=100):
        for tick in range(ticks):
            for instrument in self.instruments:
                updated = self.simulate_market_movement(instrument)
                topic = TOPIC_CDS if updated["product"] == "CDS" else TOPIC_BONDS
                self.producer.produce(
                    topic=topic,
                    key=updated["instrument_id"],
                    value=json.dumps(updated),
                    callback=self.delivery_report
                )
                self.producer.poll(0)
            time.sleep(0.1)
        self.producer.flush()

if __name__ == "__main__":
    simulator = MarketDataSimulator(num_instruments=NUM_INSTRUMENTS)
    simulator.build_universe()
    simulator.run_simulator()
