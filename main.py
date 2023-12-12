from dotenv import load_dotenv
import pandas as pd
from panel.widgets import Tabulator
import os
import panel as pn
import threading
from panel.template import FastListTemplate
from datetime import datetime
from panel.widgets import Checkbox
import time
from metaapi_cloud_sdk import MetaApi
import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
from pymongo import MongoClient  # Missing import
from panel.viewable import Layoutable  # Missing import
from panel import panel  # Missing import
from panel.pane import ECharts  # Missing import

# Load environment variables
load_dotenv()
print("Environment variables loaded.")

# Get MetaApi token and account id
api_token = os.getenv('META_API_TOKEN')
account_id = os.getenv('META_API_ACCOUNT_ID')
print("MetaApi token and account id retrieved.")

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
    print(f"Fetched positions: {fetched_positions}")

    if not fetched_positions:
        print("No positions data received.")
        return

    # Convert the fetched positions to a DataFrame
    df = pd.DataFrame(fetched_positions)
    print(f"DataFrame created with {len(df)} entries.")

    # Apply transformations to the DataFrame
    # ... (The synchronous code that fetches and updates the positions) ...

    # Apply transformations to the DataFrame
    df1 = df.groupby(['symbol', 'type']).agg({
        'volume': 'sum',
        'unrealizedProfit': 'sum',
        'swap': 'sum',
        'openPrice': lambda x: (x * df.loc[x.index, 'volume']).sum() / df.loc[x.index, 'volume'].sum(),
        'time': 'min',
        'magic': lambda x: ', '.join(f"{v}-{k}" for k, v in x.value_counts().items()),
        'comment': lambda x: ', '.join(f"{v}-{k}" for k, v in x.value_counts().items()),
        'profit': 'sum',
        'realizedProfit': 'sum',
        'unrealizedSwap': 'sum',
        'realizedSwap': 'sum',
    }).reset_index()

    df1['time'] = pd.to_datetime(df1['time'])
    df1['Days'] = (datetime.now() - df1['time']).dt.days
    df1 = df1.drop(columns=['time'])
    idx = df1.columns.get_loc('openPrice') + 1
    df1.insert(idx, 'Days', df1.pop('Days'))
    df1 = df1.rename(columns={'unrealizedProfit': 'uProfit', 'openPrice': 'BE'})
    df1['type'] = df1['type'].replace({'POSITION_TYPE_BUY': 'BUY', 'POSITION_TYPE_SELL': 'SELL'})
    # Convert 'uProfit' and 'swap' to integer
    df1['uProfit'] = df1['uProfit'].astype(int)
    df1['swap'] = df1['swap'].astype(int)

    # Update the tables completely
    positions_summary.value = df1
    positions_all_grouped.value = df[['symbol', 'type', 'volume', 'profit', 'swap', 'openPrice', 'time', 'comment', 'magic']]

# Fetch and update positions
# This is now an empty placeholder to ensure we don't run the function immediately
# The actual call to fetch_and_update_positions will be handled within the update_table function

# Initialize empty DataFrames for the Panel tables
df1 = pd.DataFrame()
df2 = pd.DataFrame()

# positions_summary - 1st table
positions_summary = pn.widgets.Tabulator(df1, page_size=40, layout='fit_columns',
                                         hidden_columns=['index', 'magic', 'comment', 'profit', 'realizedProfit', 'unrealizedSwap', 'realizedSwap'],
                                         sorters=[{'column': 'volume', 'dir': 'desc'}],
                                         sizing_mode='stretch_both',
                                         stylesheets=['assets/mystyle.css'],
                                         text_align='center')

# positions_all_grouped - 2nd table
positions_all_grouped = pn.widgets.Tabulator(df2, groupby=['symbol', 'type'])

# Create a FastGridTemplate with dark theme
template = FastListTemplate(
    title='thetradingbot',
    theme='dark',
    theme_toggle=True,
    collapsed_sidebar=True,
    sidebar_width=200,
    accent_base_color='#04282D',
    header_background='#000000',  # Change to your desired color
    logo='assets/images/ttb-logo-small-200.png',
    css_files=['assets/mystyle.css'] 
)

# Create Checkbox widgets
checkbox_magic = pn.widgets.Checkbox(name='Show magic', value=False)
checkbox_comment = pn.widgets.Checkbox(name='Show comment', value=False)
checkbox_profit = pn.widgets.Checkbox(name='Show profit', value=False)
checkbox_realizedProfit = pn.widgets.Checkbox(name='Show realizedProfit', value=False)
checkbox_unrealizedSwap = pn.widgets.Checkbox(name='Show unrealizedSwap', value=False)
checkbox_realizedSwap = pn.widgets.Checkbox(name='Show realizedSwap', value=False)

# Define callback functions
def callback_magic(event):
    hidden_columns = set(positions_summary.hidden_columns)
    if event.new:
        hidden_columns.discard('magic')
    else:
        hidden_columns.add('magic')
    positions_summary.hidden_columns = list(hidden_columns)

def callback_comment(event):
    hidden_columns = set(positions_summary.hidden_columns)
    if event.new:
        hidden_columns.discard('comment')
    else:
        hidden_columns.add('comment')
    positions_summary.hidden_columns = list(hidden_columns)

def callback_profit(event):
    hidden_columns = set(positions_summary.hidden_columns)
    if event.new:
        hidden_columns.discard('profit')
    else:
        hidden_columns.add('profit')
    positions_summary.hidden_columns = list(hidden_columns)

def callback_realizedProfit(event):
    hidden_columns = set(positions_summary.hidden_columns)
    if event.new:
        hidden_columns.discard('realizedProfit')
    else:
        hidden_columns.add('realizedProfit')
    positions_summary.hidden_columns = list(hidden_columns)

def callback_unrealizedSwap(event):
    hidden_columns = set(positions_summary.hidden_columns)
    if event.new:
        hidden_columns.discard('unrealizedSwap')
    else:
        hidden_columns.add('unrealizedSwap')
    positions_summary.hidden_columns = list(hidden_columns)

def callback_realizedSwap(event):
    hidden_columns = set(positions_summary.hidden_columns)
    if event.new:
        hidden_columns.discard('realizedSwap')
    else:
        hidden_columns.add('realizedSwap')
    positions_summary.hidden_columns = list(hidden_columns)

# Add callbacks to checkboxes
checkbox_magic.param.watch(callback_magic, 'value')
checkbox_comment.param.watch(callback_comment, 'value')
checkbox_profit.param.watch(callback_profit, 'value')
checkbox_realizedProfit.param.watch(callback_realizedProfit, 'value')
checkbox_unrealizedSwap.param.watch(callback_unrealizedSwap, 'value')
checkbox_realizedSwap.param.watch(callback_realizedSwap, 'value')

# Add to sidebar
template.sidebar.append(checkbox_magic)
template.sidebar.append(checkbox_comment)
template.sidebar.append(checkbox_profit)
template.sidebar.append(checkbox_realizedProfit)
template.sidebar.append(checkbox_unrealizedSwap)
template.sidebar.append(checkbox_realizedSwap)

# Append the tables to the main area
template.main.append(positions_summary)
template.main.append(positions_all_grouped)

# Create a stop event
stop_event = threading.Event()

def update_table():
    while not stop_event.is_set():
        print("Fetching new data from the database...")
        asyncio.run(fetch_and_update_positions())

        # Wait for a certain period of time or until the stop event is set
        stop_event.wait(60)

# Function to serve the template
def serve_template():
    pn.serve(template, static_dirs={'assets': './assets'})

# Start a new thread that runs the serve_template function
serve_thread = threading.Thread(target=serve_template)
serve_thread.start()

try:
    # Start a new thread that runs the update_table function
    update_thread = threading.Thread(target=update_table)
    update_thread.start()

    # Keep the main thread running
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    # Stop the updates when Ctrl+C is pressed
    stop_event.set()
    # Join the threads to ensure they have stopped before exiting
    update_thread.join()
    serve_thread.join()
