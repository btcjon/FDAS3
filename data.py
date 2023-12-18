import sqlite3
import asyncio
from metaapi_cloud_sdk import MetaApi
from datetime import datetime
from dotenv import load_dotenv
import os
import time

load_dotenv()

# MetaApi API token
api_token = os.getenv('META_API_TOKEN')
account_id = os.getenv('META_API_ACCOUNT_ID')

# SQLite connection
conn = sqlite3.connect('fdas/positions.db')
cursor = conn.cursor()

# Create table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS positions (
        id TEXT PRIMARY KEY,
        type TEXT,
        platform TEXT,
        symbol TEXT,
        magic INTEGER,
        time TEXT,
        brokerTime TEXT,
        updateTime TEXT,
        openPrice REAL,
        volume REAL,
        swap REAL,
        realizedSwap REAL,
        unrealizedSwap REAL,
        commission REAL,
        realizedCommission REAL,
        unrealizedCommission REAL,
        realizedProfit REAL,
        reason TEXT,
        accountCurrencyExchangeRate REAL,
        brokerComment TEXT,
        currentPrice REAL,
        currentTickValue REAL,
        unrealizedProfit REAL,
        profit REAL,
        comment TEXT,
        updateSequenceNumber INTEGER
    )
''')

async def run():
    api = MetaApi(api_token)
    account = await api.metatrader_account_api.get_account(account_id)
    connection = account.get_streaming_connection()
    await connection.connect()
    await connection.wait_synchronized()

    # Fetch positions
    positions = connection.terminal_state.positions
    print(f"{len(positions)} records fetched")

    # Create a list of ids from the fetched positions
    ids = [position.get('id') for position in positions]

    # Delete records from the database that are not in the latest fetch
    if ids:
        placeholders = ', '.join('?' for _ in ids)
        cursor.execute(f'''
            DELETE FROM positions WHERE id NOT IN ({placeholders})
        ''', ids)

    # Insert positions into SQLite database
    for position in positions:
        cursor.execute('''
            SELECT COUNT(*) FROM positions WHERE id = ?
        ''', (position.get('id'),))
        count = cursor.fetchone()[0]
        if count == 0:
            cursor.execute('''
                INSERT INTO positions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                position.get('id'),
                position.get('type'),
                position.get('platform'),
                position.get('symbol'),
                position.get('magic'),
                position.get('time'),
                position.get('brokerTime'),
                position.get('updateTime'),
                position.get('openPrice'),
                position.get('volume'),
                position.get('swap'),
                position.get('realizedSwap'),
                position.get('unrealizedSwap'),
                position.get('commission'),
                position.get('realizedCommission'),
                position.get('unrealizedCommission'),
                position.get('realizedProfit'),
                position.get('reason'),
                position.get('accountCurrencyExchangeRate'),
                position.get('brokerComment'),
                position.get('currentPrice'),
                position.get('currentTickValue'),
                position.get('unrealizedProfit'),
                position.get('profit'),
                position.get('comment'),
                position.get('updateSequenceNumber')
            ))

    # Commit changes
    conn.commit()
    print(f"{len(positions)} records updated")

# Run the async function in an infinite loop with a delay
while True:
    asyncio.run(run())
    time.sleep(60)  # wait for 60 seconds before next run
