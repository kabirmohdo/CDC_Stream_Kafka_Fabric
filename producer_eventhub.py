import os
import json
import logging
import requests
import time
from azure.eventhub import EventHubProducerClient, EventData
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Azure Event Hubs connection details from .env
CONNECTION_STRING = os.getenv("EVENTHUB_CONNECTION_STRING")
EVENTHUB_NAME = os.getenv("EVENTHUB_NAME")

# Function to fetch user data from the API
def fetch_user_data(api_url):
    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        data = response.json()
        user = data['results'][0]
        user_data = {
            "Name": f"{user['name']['title']} {user['name']['first']} {user['name']['last']}",
            "Gender": user['gender'],
            "Address": f"{user['location']['street']['number']} {user['location']['street']['name']}, {user['location']['city']}, {user['location']['state']} - {user['location']['country']} {user['location']['postcode']}",
            "Coordinates": f"Latitude {user['location']['coordinates']['latitude']}, Longitude {user['location']['coordinates']['longitude']}",
            "Timezone": f"{user['location']['timezone']['description']} (Offset {user['location']['timezone']['offset']})",
            "Email": user['email'],
            "Phone": user['phone'],
            "Cell": user['cell'],
            "Date of Birth": f"{user['dob']['date']} (Age: {user['dob']['age']})",
            "Registered": f"{user['registered']['date']} (Age: {user['registered']['age']})",
            "Picture": user['picture']['large']
        }
        return user_data
    except requests.RequestException as e:
        logging.error(f"Failed to fetch data: {str(e)}")
        return None

# Function to serialize data
def json_serializer(data):
    try:
        return json.dumps(data)
    except (TypeError, ValueError) as e:
        logging.error(f"JSON serialization error: {str(e)}")
        return None

# Function to create the Event Hub producer
def create_producer():
    try:
        return EventHubProducerClient.from_connection_string(conn_str=CONNECTION_STRING, eventhub_name=EVENTHUB_NAME)
    except Exception as e:
        logging.error(f"Failed to create Event Hub producer: {str(e)}")
        return None

# Main function to fetch data and send to Event Hub
def main():
    api_url = "https://randomuser.me/api/"
    producer = create_producer()
    if not producer:
        logging.error("Exiting due to Event Hub producer creation failure")
        return

    try:
        while True:
            logging.info("Fetching and sending data to Event Hub...")
            user_data = fetch_user_data(api_url)
            if user_data:
                serialized_data = json_serializer(user_data)
                if serialized_data:
                    event_data = EventData(serialized_data)
                    event_batch = producer.create_batch()
                    try:
                        event_batch.add(event_data)  # Correct usage of add() instead of try_add()
                        logging.info(f"Sending user data to Event Hub: {user_data}")
                        producer.send_batch(event_batch)
                    except ValueError:
                        logging.error("Event too large to send in a batch.")
                else:
                    logging.error("Failed to serialize data.")
            else:
                logging.error("Failed to fetch user data.")
            # Pause for 10 seconds between API calls
            time.sleep(10)
    except KeyboardInterrupt:
        logging.info("Process terminated by user. Exiting...")
    finally:
        if producer:
            producer.close()

if __name__ == "__main__":
    main()
