import os
import asyncio
import json
import logging
from metaapi_cloud_sdk import MetaApi, SynchronizationListener
from datetime import datetime, timedelta
from dotenv import load_dotenv
from airtable import Airtable
from collections import defaultdict

load_dotenv()

token = os.getenv('TOKEN')
accountId = os.getenv('ACCOUNT_ID')

# Initialize Airtable client for the 'Positions' table
airtable_api_key = os.getenv('AIRTABLE_API_KEY')
airtable_base_id = os.getenv('AIRTABLE_BASE_ID')
airtable_table_name = 'Positions'
airtable = Airtable(airtable_base_id, airtable_table_name, api_key=airtable_api_key)

def convert_position_to_airtable_format(position, existing_record=None):
    # Convert position data to match Airtable structure
    airtable_position = {
        'Symbol': position['symbol'],
        'Type': position['type'],
        'Volume': position['volume'],
        'Profit': position['profit'],
        'Swap': position['swap'],
        'Commission': position['commission'],
        'Count': position.get('Count', ''),  # Use an empty string if 'Count' is not in position
        'Oldest': position.get('Oldest', ''),  # Use an empty string if 'Oldest' is not in position
        'Comments': position.get('Comments', ''),  # Use an empty string if 'Comments' is not in position
    }
    # If there is an existing record, append the new time to the 'Times' field
    if existing_record:
        airtable_position['Times'] = existing_record['fields'].get('Times', '') + ',' + str(position['time'])
    else:
        airtable_position['Times'] = str(position['time'])
    return airtable_position

class MySynchronizationListener(SynchronizationListener):
    def __init__(self, existing_records):
        self.existing_records_dict = {(record['fields']['Symbol'], record['fields']['Type']): record for record in existing_records}

    async def on_position_update(self, accountId, position):
        print(f"Received position update: {position}")
        # Update your Airtable records here
        key = (position['symbol'], position['type'])
        airtable_position = convert_position_to_airtable_format(position, self.existing_records_dict.get(key))
        key = (position['symbol'], position['type'])
        if key in self.existing_records_dict:
            # Update the existing record
            airtable.update(self.existing_records_dict[key]['id'], airtable_position)
        else:
            # Insert a new record
            airtable.insert(airtable_position)

async def main():
    # Initialize MetaApi first
    api = MetaApi(token)

    # Get the MetaTrader account
    account = await api.metatrader_account_api.get_account(accountId)
    print(f"Got account: {account}")

    # Get a streaming connection for the account
    connection = account.get_streaming_connection()
    print(f"Got streaming connection: {connection}")

    # Connect to the server
    await connection.connect()

    # Wait until the connection is synchronized
    await connection.wait_synchronized()


    # Fetch the initial state of the positions
    positions = connection.terminal_state.positions
    for position in positions:
        # Define the key
        key = (position['symbol'], position['type'])
        # Update your Airtable records here
        airtable_position = convert_position_to_airtable_format(position, existing_records_dict.get(key))
        if key in existing_records_dict:
            # Update the existing record
            airtable.update(existing_records_dict[key]['id'], airtable_position)
        else:
            # Insert a new record
            airtable.insert(airtable_position)

    # Fetch all existing records from the 'Positions' table
    existing_records = airtable.get_all()
    # Add a synchronization listener to the connection with existing records
    listener = MySynchronizationListener(existing_records)
    connection.add_synchronization_listener(listener)

    # The infinite loop and periodic checks are removed as we are now using event-driven updates.
    # The connection health check will be implemented as an optional feature.

asyncio.run(main())
async def periodic_connection_health_check(connection, interval=300):
    """Periodically checks the connection health and reconnects if necessary."""
    while True:
        if not connection.connected:
            print("Connection lost, reconnecting...")
            await connection.connect()
            await connection.wait_synchronized()
        else:
            print(f"Connection is alive. Next check in {interval} seconds.")
        await asyncio.sleep(interval)

# At the end of the main function, you can start the health check coroutine if needed:
# asyncio.create_task(periodic_connection_health_check(connection, 600))
