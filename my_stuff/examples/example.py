import os
import asyncio
from metaapi_cloud_sdk import MetaApi
from datetime import datetime

# Note: for information on how to use this example code please read https://metaapi.cloud/docs/client/usingCodeExamples

token = os.getenv('TOKEN') or 'eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCJ9.eyJfaWQiOiIyODQxMmYzMTYwN2Y4ZTEyOTc0NGM4MDkwNmRhMjQ4ZiIsInBlcm1pc3Npb25zIjpbXSwidG9rZW5JZCI6IjIwMjEwMjEzIiwiaW1wZXJzb25hdGVkIjpmYWxzZSwicmVhbFVzZXJJZCI6IjI4NDEyZjMxNjA3ZjhlMTI5NzQ0YzgwOTA2ZGEyNDhmIiwiaWF0IjoxNzAyNDcxNzYwfQ.n44uV3GvTpP274SpHY3-AeDpvCTA0nmvXhPco8g7PH-0TnANBZzZaf3oTE8lxTrPXNyI9lb2Y7KXjH5OwncfuuqYqxsMnZMH79D2YgD3ZItGY_ttOeo9EIJAXp-5EcTsqi-z6BvTKphXJOUSw0eAJqNRcgsxEYVJix7b6q6BgZIWtRQVaTtffYoS4_nie9qeXiRJKSOpEz7YiUlC7oMZRtffVCVAzyAKe3Kuj1aTjfFagTeNTE25LpfmvPZT_2mWnhnOFNlZRJHcpa5xCGLBajwlv3QDPVQMY-CqDRWMYOtftod1XU5xLV80ekWijhwVbgHAh7SDyXy5ENFu9yDFRb9Dyhi5XduFd0etQ9hpQ69RkWwzMIMzAknJ-AOQtGcbKV0zkGFjWELemEExuMF8OcD2pNb4TRn8-L-mtQ2H3k7ZXv9YKA8af75UTPFoX_mDtVPetVIQ8fdfwMj0CkoDe5xZsdUA0krawIGb8kKgN75LP1x9LxG9ZHBN-kExcH9XbG359zR5I4h272BLw1SYdqDQcEdMwzzjSjuynR5-iycU-eTp2rRjvPoTdT5IGvOivzZdesT7806QW3KB4RbaGSsWiVlb3nC3qKYCHONCPGbQHSufruyjytjAZTogHJxnxRBoWbeyP6XUKVrGcBZbeCIzcdyN06OJaj330jMKozM'
accountId = os.getenv('ACCOUNT_ID') or '28c98cc1-cc61-4220-8a39-e4896ad746a5'


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
        print('account information:', terminal_state.account_information)
        print('positions:', terminal_state.positions)
        print('orders:', terminal_state.orders)
        print('specifications:', terminal_state.specifications)
        print('EURUSD specification:', terminal_state.specification('EURUSD'))
        await connection.subscribe_to_market_data('EURUSD')
        print('EURUSD price:', terminal_state.price('EURUSD'))

        # access history storage
        history_storage = connection.history_storage
        print('deals:', history_storage.deals[-5:])
        print('deals with id=1:', history_storage.get_deals_by_ticket('1'))
        print('deals with positionId=1:', history_storage.get_deals_by_position('1'))
        print(
            'deals for the last day:',
            history_storage.get_deals_by_time_range(
                datetime.fromtimestamp(datetime.now().timestamp() - 24 * 60 * 60), datetime.now()
            ),
        )

        print('history orders:', history_storage.history_orders[-5:])
        print('history orders with id=1:', history_storage.get_history_orders_by_ticket('1'))
        print('history orders with positionId=1:', history_storage.get_history_orders_by_position('1'))
        print(
            'history orders for the last day:',
            history_storage.get_history_orders_by_time_range(
                datetime.fromtimestamp(datetime.now().timestamp() - 24 * 60 * 60), datetime.now()
            ),
        )

        # calculate margin required for trade
        print(
            'margin required for trade',
            await connection.calculate_margin(
                {'symbol': 'GBPUSD', 'type': 'ORDER_TYPE_BUY', 'volume': 0.1, 'openPrice': 1.1}
            ),
        )

        # trade
        print('Submitting pending order')
        try:
            result = await connection.create_limit_buy_order(
                'GBPUSD', 0.07, 1.0, 0.9, 2.0, {'comment': 'comm', 'clientId': 'TE_GBPUSD_7hyINWqAlE'}
            )
            print('Trade successful, result code is ' + result['stringCode'])
        except Exception as err:
            print('Trade failed with error:')
            print(api.format_error(err))

        if initial_state not in deployed_states:
            # undeploy account if it was undeployed
            print('Undeploying account')
            await connection.close()
            await account.undeploy()

    except Exception as err:
        print(api.format_error(err))
    exit()


asyncio.run(test_meta_api_synchronization())
