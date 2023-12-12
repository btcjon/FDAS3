from metaapi_cloud_sdk import MetaApi
from dotenv import load_dotenv
from pymongo import MongoClient
from apscheduler.schedulers.background import BackgroundScheduler
import os
import asyncio
import time

# Load environment variables
load_dotenv()
print("Environment variables loaded.")

# Get MetaApi token and account id
api_token = os.getenv('META_API_TOKEN')
account_id = os.getenv('META_API_ACCOUNT_ID')
print("MetaApi token and account id retrieved.")

# Get MongoDB URI and database name
mongodb_uri = os.getenv('MONGODB_URI')
db_name = os.getenv('DB_NAME')
print("MongoDB URI and database name retrieved.")

# Create a MongoDB client
client = MongoClient(mongodb_uri)
db = client[db_name]

# Create a MongoDB collection for positions
positions_collection = db['positions']

print("MongoDB client and collections created.")

async def fetch_and_update_positions():
    # Create a MetaApi instance
    api = MetaApi(api_token)
    print("MetaApi instance created.")

    # Fetch account and create a streaming connection
    account = await api.metatrader_account_api.get_account(account_id)
    connection = account.get_streaming_connection()
    await connection.connect()

    # Wait until synchronization completed
    await connection.wait_synchronized()

    # Access local copy of terminal state
    terminalState = connection.terminal_state

    # Access positions from the terminal state
    fetched_positions = terminalState.positions
    print("Account and positions fetched.")

    # Store positions in MongoDB and create a list of fetched position ids
    fetched_position_ids = []
    for position in fetched_positions:
        positions_collection.update_one({'id': position['id']}, {"$set": position}, upsert=True)
        fetched_position_ids.append(position['id'])
    print(f"{len(fetched_positions)} positions updated or inserted in MongoDB.")

    # Fetch all positions from the database
    db_positions = positions_collection.find()

    # Remove positions from the database that are not in the fetched positions
    for db_position in db_positions:
        if db_position['id'] not in fetched_position_ids:
            positions_collection.delete_one({'id': db_position['id']})
    print("Positions not in the fetched data have been removed from the database.")

async def fetch_and_update_account_info():
    # Create a MetaApi instance
    api = MetaApi(api_token)
    print("MetaApi instance created.")

    # Fetch account and create a streaming connection
    account = await api.metatrader_account_api.get_account(account_id)
    connection = account.get_streaming_connection()
    await connection.connect()

    # Wait until synchronization completed
    await connection.wait_synchronized()

    # Access local copy of terminal state
    terminalState = connection.terminal_state

    # Access account information from the terminal state
    account_info = terminalState.account_information
    print("Account information fetched.")

    # Create a new MongoDB collection for account information
    account_info_collection = db['account_information']

    # Store account information in MongoDB
    account_info_collection.update_one({'id': account_id}, {"$set": account_info}, upsert=True)
    print("Account information updated or inserted in MongoDB.")

# Create a background scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(lambda: asyncio.run(fetch_and_update_positions()), 'interval', minutes=1)  # Adjust the interval as needed
scheduler.add_job(lambda: asyncio.run(fetch_and_update_account_info()), 'interval', minutes=5)  # Adjust the interval as needed
scheduler.start()

if __name__ == '__main__':
    asyncio.run(fetch_and_update_positions())
    asyncio.run(fetch_and_update_account_info())
    while True:
        time.sleep(15)  # Sleep for 1 second to prevent high CPU usage