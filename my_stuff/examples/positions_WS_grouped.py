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
        'Count': int(position.get('Count', 0)),  # Use 0 if 'Count' is not in position and ensure it's an integer
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

# Define connection at the top level to ensure it's accessible throughout the script
connection = None

async def main():
    global connection, account
    api = MetaApi(token)
    account = await api.metatrader_account_api.get_account(accountId)
    print(f"Got account: {account}")
    # Ensure that the connection is initialized here
    if not connection:
        connection = account.get_streaming_connection()
        print(f"Got streaming connection: {connection}")
        await connection.connect()

    # Wait until the connection is synchronized
    if connection:
        await connection.wait_synchronized()


    # Fetch all existing records from the 'Positions' table
    existing_records = airtable.get_all()
    existing_records_dict = {(record['fields']['Symbol'], record['fields']['Type']): record for record in existing_records}

    # Fetch the initial state of the positions and aggregate them by symbol and type
    positions = connection.terminal_state.positions
    aggregated_positions = defaultdict(lambda: defaultdict(float))
    for position in positions:
        key = (position['symbol'], position['type'])
        aggregated_positions[key]['symbol'] = position['symbol']
        aggregated_positions[key]['type'] = position['type']
        aggregated_positions[key]['volume'] += position.get('volume', 0)
        aggregated_positions[key]['profit'] += position.get('profit', 0)
        aggregated_positions[key]['swap'] += position.get('swap', 0)
        aggregated_positions[key]['commission'] += position.get('commission', 0)
        time_str = str(position['time'])
        if 'times' not in aggregated_positions[key] or not aggregated_positions[key]['times']:
            aggregated_positions[key]['times'] = time_str
        else:
            aggregated_positions[key]['times'] += ', ' + time_str
        if 'Count' not in aggregated_positions[key]:
            aggregated_positions[key]['Count'] = 1
        else:
            aggregated_positions[key]['Count'] += 1
        if 'Oldest' not in aggregated_positions[key] or time_str < aggregated_positions[key]['Oldest']:
            aggregated_positions[key]['Oldest'] = time_str
        comment_str = str(position.get('comment', 'na')) if position.get('comment') is not None else 'na'
        if 'Comments' not in aggregated_positions[key] or not aggregated_positions[key]['Comments']:
            aggregated_positions[key]['Comments'] = comment_str
        else:
            aggregated_positions[key]['Comments'] += ', ' + comment_str

    # Update existing records or insert new records in Airtable based on the aggregated positions
    for key, aggregated_position in aggregated_positions.items():
        airtable_position = convert_position_to_airtable_format(aggregated_position, existing_records_dict.get(key))
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

    # Start the health check coroutine to periodically check the connection health:
    asyncio.create_task(periodic_connection_health_check(account, connection, 600))

async def periodic_connection_health_check(account, interval=300):
    """Periodically checks the connection health and reconnects if necessary."""
    global connection
    api = MetaApi(token)
    while True:
        # Check if the connection object is not None and is not connected
        if connection and not connection.is_connected():
            print("Connection lost, reconnecting...")
            await connection.connect()
            await connection.wait_synchronized()
        elif connection is None:
            # Attempt to reinitialize the connection if it is None
            print("Connection object is None, attempting to reinitialize...")
            if account is None:
                try:
                    account = await api.metatrader_account_api.get_account(accountId)
                except Exception as e:
                    print(f"Failed to retrieve account: {e}")
                    await asyncio.sleep(interval)
                    continue
            if account:
                connection = account.get_streaming_connection()
                await connection.connect()
                await connection.wait_synchronized()
        else:
            print(f"Connection is alive. Next check in {interval} seconds.")
        await asyncio.sleep(interval)

# Use a try-except block to handle potential exceptions during the main coroutine
async def main():
    # ... (rest of the main function code) ...
    # At the end of the main function, start the health check coroutine:
    asyncio.create_task(periodic_connection_health_check(account, connection, 600))

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Check if 'connection' is defined and is not None before attempting to close it
        if 'connection' in globals() and connection:
            print("Closing connection...")
            asyncio.run(connection.close())
# Remove the incorrectly indented docstring and ensure the function definition is correct
async def periodic_connection_health_check(connection, interval=300):
    """Periodically checks the connection health and reconnects if necessary."""
    while True:
        if connection is None or not connection.is_connected():
            if connection is not None:
                print("Connection lost, reconnecting...")
                await connection.connect()
                await connection.wait_synchronized()
            else:
                print("Connection object is None, cannot reconnect.")
        else:
            print(f"Connection is alive. Next check in {interval} seconds.")
        await asyncio.sleep(interval)

# This block should be removed as it's incorrectly placed outside of the main coroutine.
