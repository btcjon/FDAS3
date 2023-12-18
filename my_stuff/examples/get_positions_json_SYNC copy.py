import os
import asyncio
import json
from metaapi_cloud_sdk import MetaApi
from metaapi_cloud_sdk.clients.metaApi.tradeException import TradeException
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Note: for information on how to use this example code please read https://metaapi.cloud/docs/client/usingCodeExamples

token = os.getenv('TOKEN') or '<put in your token here>'
accountId = os.getenv('ACCOUNT_ID') or '<put in your account id here>'


async def test_meta_api_synchronization():
    api = MetaApi(token)
    try:
        account = await api.metatrader_account_api.get_account(accountId)
        initial_state = account.state
        deployed_states = ['DEPLOYING', 'DEPLOYED']

        if initial_state not in deployed_states:
            #  wait until account is deployed and connected to broker
            print('Deploying account')
            await account.deploy()

        print('Waiting for API server to connect to broker (may take couple of minutes)')
        await account.wait_connected()

        # connect to MetaApi API
        connection = account.get_streaming_connection()
        await connection.connect()

        # wait until terminal state synchronized to the local state
        print('Waiting for SDK to synchronize to terminal state (may take some time depending on your history size)')
        await connection.wait_synchronized()

        # access local copy of terminal state
        print('Testing terminal state access')
        terminal_state = connection.terminal_state
        print('connected:', terminal_state.connected)
        print('connected to broker:', terminal_state.connected_to_broker)
        #print('positions:', terminal_state.positions)

        # Save positions to a JSON file
        with open('get_positions_SYNC.json', 'w') as f:
            positions = [{**item, 'time': item['time'].isoformat(), 'updateTime': item['updateTime'].isoformat()} if 'time' in item and 'updateTime' in item else item for item in terminal_state.positions]
            json.dump(positions, f)

    except Exception as err:
        print(api.format_error(err))
    exit()

asyncio.run(test_meta_api_synchronization())


