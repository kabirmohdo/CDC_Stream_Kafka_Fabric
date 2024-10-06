import os
import json
import logging
from kafka import KafkaConsumer
from kafka.errors import KafkaError
from azure.storage.filedatalake import DataLakeServiceClient
from azure.core.exceptions import AzureError
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to create a Kafka Consumer
def create_kafka_consumer(topic):
    try:
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=['localhost:9093'],
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            group_id='my-group-id',
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        logging.info("Kafka Consumer created successfully.")
        return consumer
    except KafkaError as e:
        logging.error(f"Failed to create Kafka consumer: {str(e)}")
        return None

# Function to upload the JSON file to Azure Data Lake Gen 2 using SAS token
def upload_to_datalake_gen2(json_data, filename):
    try:
        # Get SAS token and account information from environment variables
        account_name = os.getenv("account_name")
        file_system_name = os.getenv("file_system_name")
        sas_token = os.getenv("sas_token")

        # Log the values for debugging
        logging.info(f"Account Name: {account_name}")
        logging.info(f"File System Name: {file_system_name}")
        logging.info(f"SAS Token: {sas_token[:10]}...")  # Log only the first few characters of the SAS token

        # Ensure file_system_name is not None or empty
        if not file_system_name:
            raise ValueError("File system name is not specified or is empty.")

        # Create the service client using the SAS token
        service_client = DataLakeServiceClient(account_url=f"https://{account_name}.dfs.core.windows.net", credential=sas_token)

        # Get the file system (container) client
        file_system_client = service_client.get_file_system_client(file_system=file_system_name)

        # Create a new file in the specified directory
        file_path = f"randomuserjson/{filename}"
        file_client = file_system_client.get_file_client(file_path)

        # Upload the JSON data to the file
        file_contents = json.dumps(json_data)
        file_client.upload_data(file_contents, overwrite=True)

        logging.info(f"File {file_path} uploaded to Azure Data Lake Gen 2 successfully.")
    except ValueError as ve:
        logging.error(f"ValueError: {str(ve)}")
    except AzureError as ae:
        logging.error(f"AzureError: {str(ae)}")
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")

# Main function to consume messages from Kafka and send them to Azure Data Lake
def main():
    topic = "fabric_deb_conn.fabric.user_data"
    consumer = create_kafka_consumer(topic)
    if not consumer:
        logging.error("Exiting due to Kafka consumer creation failure.")
        return

    try:
        for message in consumer:
            user_data = message.value
            logging.info(f"Received user data: {user_data}")

            # Generate a unique filename using timestamp or UUID
            filename = f"user_data_{message.timestamp}.json"

            # Upload to Azure Data Lake Gen 2
            upload_to_datalake_gen2(user_data, filename)

    except KeyboardInterrupt:
        logging.info("Process terminated by user.")
    finally:
        consumer.close()

if __name__ == "__main__":
    main()
