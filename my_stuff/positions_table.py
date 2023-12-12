from dotenv import load_dotenv
from pymongo import MongoClient
import pandas as pd
from panel.widgets import Tabulator
import os
import panel as pn
import threading
from panel.viewable import Layoutable
from panel.template import FastListTemplate
from datetime import datetime
from panel.widgets import Checkbox
import time
from panel import panel
import plotly.graph_objects as go


# Load environment variables
load_dotenv()
print("Environment variables loaded.")

# Get MongoDB URI and database name
mongodb_uri = os.getenv('MONGODB_URI')
db_name = os.getenv('DB_NAME')
print("MongoDB URI and database name retrieved.")

# Create a MongoDB client
client = MongoClient(mongodb_uri)
db = client[db_name]
collection = db['positions']
print("MongoDB client created.")



# account info tabulator
# Fetch data from the 'account_information' collection
account_info_collection = db['account_information']
df_account_info = pd.DataFrame(list(account_info_collection.find()))

# Convert ObjectId instances to strings
df_account_info['_id'] = df_account_info['_id'].astype(str)

balance = pn.pane.Markdown(f'**Balance**: {df_account_info["balance"].values[0]}', margin=(0, 0, 5, 0))
equity = pn.pane.Markdown(f'**Equity**: {df_account_info["equity"].values[0]}', margin=(0, 0, 5, 0))
marginLevel = pn.pane.Markdown(f'**Margin Level**: {df_account_info["marginLevel"].values[0]}', margin=(0, 0, 5, 0))

account_info_display = pn.Column(balance, equity, marginLevel)



# Create a gauge chart
# Get margin level
# Get margin level
margin_level = int(round(df_account_info["marginLevel"].values[0]))

gauge = {
    'series': [
        {
            'type': 'gauge',
            'center': ['50%', '60%'],
            'startAngle': 200,
            'endAngle': -20,
            'min': 0,
            'max': 5000,
            'splitNumber': 10,
            'itemStyle': {
                'color': '#FFAB91'
            },
            'progress': {
                'show': True,
                'width': 30
            },
            'pointer': {
                'show': False
            },
            'axisLine': {
                'lineStyle': {
                    'width': 30
                }
            },
            'axisTick': {
                'distance': -45,
                'splitNumber': 5,
                'lineStyle': {
                    'width': 2,
                    'color': '#999'
                }
            },
            'splitLine': {
                'distance': -52,
                'length': 14,
                'lineStyle': {
                    'width': 3,
                    'color': '#999'
                }
            },
            'axisLabel': {
                'distance': -20,
                'color': '#999',
                'fontSize': 8  # Adjust this to make the text smaller
            },
            'anchor': {
                'show': False
            },
            'title': {
                'show': False
            },
            'detail': {
                'valueAnimation': True,
                'width': '60%',
                'lineHeight': 40,
                'borderRadius': 8,
                'offsetCenter': [0, '-15%'],
                'fontSize': 12,  # Adjust this to make the text smaller
                'fontWeight': 'bolder',
                'formatter': '{value}',
                'color': 'inherit'
            },
            'data': [
                {
                    'value': round(margin_level)
                }
            ]
        },
        {
            'type': 'gauge',
            'center': ['50%', '60%'],
            'startAngle': 200,
            'endAngle': -20,
            'min': 0,
            'max': 5000,  # Adjust this to a multiple of 8-10
            'itemStyle': {
                'color': '#FD7347'
            },
            'progress': {
                'show': True,
                'width': 8
            },
            'pointer': {
                'show': False
            },
            'axisLine': {
                'show': False
            },
            'axisTick': {
                'show': False
            },
            'splitLine': {
                'show': False
            },
            'axisLabel': {
                'show': False
            },
            'detail': {
                'show': False
            },
            'data': [
                {
                    'value': round(margin_level)
                }
            ]
        }
    ]
}

# Create the pane
gauge_pane = pn.pane.ECharts(gauge, width=150, height=150)




# Create a Panel table
df = pd.DataFrame(list(collection.find()))
 # Convert ObjectId instances to strings
df['_id'] = df['_id'].astype(str) 
# This will print the first 5 rows of the DataFrame
print(df.head())  

# Group by 'symbol' and 'type', and aggregate the other columns for df1
df1 = df.groupby(['symbol', 'type']).agg({
    'volume': 'sum',
    'unrealizedProfit': 'sum',
    'swap': 'sum',
    'openPrice': lambda x: (x * df.loc[x.index, 'volume']).sum() / df.loc[x.index, 'volume'].sum(),
    'time': 'min',  # Get the oldest time
    'magic': lambda x: ', '.join(f"{v}-{k}" for k, v in x.value_counts().items()),
    'comment': lambda x: ', '.join(f"{v}-{k}" for k, v in x.value_counts().items()),
    'profit': 'sum',
    'realizedProfit': 'sum',
    'unrealizedSwap': 'sum',
    'realizedSwap': 'sum',
}).reset_index()

# Ensure 'time' is in datetime format
df1['time'] = pd.to_datetime(df1['time'])

# Calculate 'Days'
df1['Days'] = (datetime.now() - df1['time']).dt.days

# Drop the 'time' column
df1 = df1.drop(columns=['time'])

# Get the current index of 'openPrice' and add 1 to place 'Days' right after it
idx = df1.columns.get_loc('openPrice') + 1

# Move 'Days' to right after 'openPrice'
df1.insert(idx, 'Days', df1.pop('Days'))

# rename columns for readability
df1 = df1.rename(columns={'unrealizedProfit': 'uProfit', 'openPrice': 'BE'})

# make 'type' prettier
df1['type'] = df1['type'].replace({'POSITION_TYPE_BUY': 'BUY', 'POSITION_TYPE_SELL': 'SELL'})

#disables editing in all columns
tabulator_editors = {col: None for col in df1.columns}

def color_conditions(row):
    """
    Colors 'BUY' and certain symbols in orange and yellow.
    """
    conditions = {
        'orange': [
            ('USDCHF.PRO', 'SELL'),
            ('EURUSD.PRO', 'BUY'),
            ('GBPAUD.PRO', 'SELL'),
            ('AUDCHF.PRO', 'BUY'),
            ('GBPCHF.PRO', 'BUY'),
            ('NZDCHF.PRO', 'BUY'),
            ('NZDJPY.PRO', 'BUY'),
            ('USDCAD.PRO', 'SELL'),
            ('GBPAUD.PRO', 'BUY'),
            ('AUDJPY.PRO', 'BUY'),
            ('NZDJPY.PRO', 'SELL'),
            ('GBPNZD.PRO', 'BUY'),
            ('EURAUD.PRO', 'BUY')
        ],
        'yellow': [
            ('USDJPY.PRO', 'SELL'),
            ('AUDUSD.PRO', 'BUY'),
            ('NZDUSD.PRO', 'BUY'),
            ('EURCAD.PRO', 'SELL'),
            ('AUDNZD.PRO', 'BUY'),
            ('GBPJPY.PRO', 'SELL'),
            ('AUDCAD.PRO', 'SELL'),
            ('GBPJPY.PRO', 'BUY')
        ]
    }

    for color, cond in conditions.items():
        if (row['symbol'], row['type']) in cond:
            return pd.Series(f'color: {color}', row.index)
    return pd.Series('color: white', row.index)

def color_negative_red(val):
    """
    Takes a scalar and returns a string with
    the css property `'color: red'` for negative
    strings, black otherwise.
    """
    color = '#F963B0' if val < 0 else '#62FACC'
    return 'color: %s' % color


df1 = df1.style.apply(color_conditions, axis=1).applymap(color_negative_red, subset=['uProfit', 'swap'])

# positions_summary df1 - 1st table
positions_summary = pn.widgets.Tabulator(df1, page_size=40, layout='fit_columns', 
                                         hidden_columns=['index', 'magic', 'comment', 'profit', 'realizedProfit', 'unrealizedSwap', 'realizedSwap'], 
                                         sorters=[{'column': 'volume', 'dir': 'desc'}],
                                         editors=tabulator_editors, 
                                         sizing_mode='stretch_both', 
                                         stylesheets=['assets/mystyle.css'], 
                                         text_align='center', # Add the style parameter
                                         )




#start checkboxes to show
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

# positions_all df2 - 2nd table
df2 = df[['symbol', 'type', 'volume', 'profit', 'swap', 'openPrice', 'time', 'comment', 'magic']]
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



# Add to sidebar
template.sidebar.append(balance)
template.sidebar.append(equity)
template.sidebar.append(marginLevel)
template.sidebar.append(checkbox_magic)
template.sidebar.append(checkbox_comment)
template.sidebar.append(checkbox_profit)
template.sidebar.append(checkbox_realizedProfit)
template.sidebar.append(checkbox_unrealizedSwap)
template.sidebar.append(checkbox_realizedSwap)
# Append the tables to the main area
#template.main.append(account_info_display)
template.main.append(gauge_pane)
template.main.append(positions_summary)
template.main.append(positions_all_grouped)


# Create a stop event
stop_event = threading.Event()

def update_table():
    while not stop_event.is_set():
        print("Fetching new data from the database...")
        # Fetch new data from the database
        df = pd.DataFrame(list(collection.find()))
        df['_id'] = df['_id'].astype(str)  # Convert ObjectId instances to strings

        # Apply the same transformations as were applied to the original DataFrame
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
