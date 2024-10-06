import os
import json
from kafka import KafkaConsumer
from elasticsearch import Elasticsearch
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration from .env
KAFKA_TOPIC = 'fabric_deb_conn.fabric.user_data'
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS')
ES_HOSTS = os.getenv('ES_HOSTS')
ES_INDEX = 'user_data_index_new'

# Connect to Elasticsearch
def connect_to_elasticsearch():
    es = Elasticsearch(ES_HOSTS)
    if es.ping():
        logging.info('Connected to Elasticsearch')
    else:
        raise ConnectionError("Unable to connect to Elasticsearch")
    return es

# Function to create Elasticsearch index if it doesn't exist
def create_index(es):
    index_body = {
        "mappings": {
            "properties": {
                "id": {"type": "integer"},
                "name": {"type": "text"},
                "gender": {"type": "keyword"},
                "address": {"type": "text"},
                "latitude": {"type": "float"},
                "longitude": {"type": "float"},
                "timezone": {"type": "text"},
                "email": {"type": "keyword"},
                "phone": {"type": "keyword"},
                "cell": {"type": "keyword"},
                "date_of_birth": {"type": "date"},
                "registered_date": {"type": "date"},
                "picture_url": {"type": "keyword"},
                "insertion_time": {"type": "date"}
            }
        }
    }

    if not es.indices.exists(index=ES_INDEX):
        es.indices.create(index=ES_INDEX, body=index_body)
        logging.info(f"Elasticsearch index '{ES_INDEX}' created.")
    else:
        logging.info(f"Elasticsearch index '{ES_INDEX}' already exists.")

# Parse Kafka message payload to usable dictionary
def parse_kafka_message(message):
    try:
        # No need to decode, message.value is already a string
        payload = json.loads(message.value)
        
        if 'after' in payload['payload'] and payload['payload']['after']:
            return payload['payload']['after']
        else:
            logging.warning("Received message without 'after' field or with no data.")
            return None
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding Kafka message: {e}")
        return None

# Function to insert data into Elasticsearch
def insert_data_into_elasticsearch(es, data):
    if data:
        es.index(index=ES_INDEX, body=data)
        logging.info(f"Inserted data into Elasticsearch: {data}")
    else:
        logging.error("No valid data to insert into Elasticsearch")

# Main Kafka consumer function
def consume_from_kafka():
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        value_deserializer=lambda x: x.decode('utf-8')
    )

    es = connect_to_elasticsearch()
    create_index(es)

    logging.info(f"Listening to Kafka topic: {KAFKA_TOPIC}")

    try:
        for message in consumer:
            logging.info(f"Received message from Kafka: {message}")
            data = parse_kafka_message(message)
            if data:
                # Insert the parsed data into Elasticsearch
                insert_data_into_elasticsearch(es, data)
    except KeyboardInterrupt:
        logging.info("Consumer interrupted. Exiting...")
    finally:
        consumer.close()

# Entry point
if __name__ == '__main__':
    consume_from_kafka()
