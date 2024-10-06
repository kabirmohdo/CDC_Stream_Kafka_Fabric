import requests
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
import time
import logging
from datetime import datetime

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# SQLAlchemy setup
Base = declarative_base()

class UserData(Base):
    __tablename__ = 'user_data'
    __table_args__ = {'schema': 'fabric'}

    id = Column(Integer, primary_key=True)
    name = Column(String)
    gender = Column(String)
    address = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    timezone = Column(String)
    email = Column(String)
    phone = Column(String)
    cell = Column(String)
    date_of_birth = Column(DateTime)
    registered_date = Column(DateTime)
    picture_url = Column(String)
    insertion_time = Column(DateTime, default=datetime.utcnow)

# Function to fetch user data from the API
def fetch_user_data(api_url):
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
        user = data['results'][0]
        
        user_data = {
            "Name": f"{user['name']['title']} {user['name']['first']} {user['name']['last']}",
            "Gender": user['gender'],
            "Address": f"{user['location']['street']['number']} {user['location']['street']['name']}, {user['location']['city']}, {user['location']['state']} - {user['location']['country']} {user['location']['postcode']}",
            "Latitude": user['location']['coordinates']['latitude'],
            "Longitude": user['location']['coordinates']['longitude'],
            "Timezone": f"{user['location']['timezone']['description']} (Offset {user['location']['timezone']['offset']})",
            "Email": user['email'],
            "Phone": user['phone'],
            "Cell": user['cell'],
            "Date of Birth": user['dob']['date'],
            "Registered": user['registered']['date'],
            "Picture": user['picture']['large']
        }
        return user_data
    except requests.RequestException as e:
        logging.error(f"Failed to fetch data: {str(e)}")
        return None

# Function to create database engine
def create_db_engine():
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        raise ValueError("DATABASE_URL not found in environment variables")
    return create_engine(db_url)

# Function to insert data into the database
def insert_data_to_db(engine, data):
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        new_user = UserData(
            name=data['Name'],
            gender=data['Gender'],
            address=data['Address'],
            latitude=float(data['Latitude']),
            longitude=float(data['Longitude']),
            timezone=data['Timezone'],
            email=data['Email'],
            phone=data['Phone'],
            cell=data['Cell'],
            date_of_birth=datetime.strptime(data['Date of Birth'], "%Y-%m-%dT%H:%M:%S.%fZ"),
            registered_date=datetime.strptime(data['Registered'], "%Y-%m-%dT%H:%M:%S.%fZ"),
            picture_url=data['Picture']
        )
        session.add(new_user)
        session.commit()
        logging.info("Data successfully inserted into the database")
    except Exception as e:
        session.rollback()
        logging.error(f"Error inserting data into database: {str(e)}")
    finally:
        session.close()

# Main function to fetch data and insert into database
def main():
    api_url = "https://randomuser.me/api/"
    engine = create_db_engine()
    
    # Create tables if they don't exist
    Base.metadata.create_all(engine)
    
    try:
        while True:
            user_data = fetch_user_data(api_url)
            if user_data:
                df = pd.DataFrame([user_data])
                logging.info(f"Fetched user data: \n{df}")
                insert_data_to_db(engine, user_data)
            
            logging.info("Waiting for 5 seconds before next insertion...")
            time.sleep(5)
    except KeyboardInterrupt:
        logging.info("Process terminated by user (Ctrl+C). Exiting...")

if __name__ == "__main__":
    main()