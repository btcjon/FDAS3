import reflex
import pandas as pd
import requests
import os
from dotenv import load_dotenv

# Load the .env file
load_dotenv()

# Get the token from the environment variable
token = os.getenv('TOKEN')

headers = {
    'auth-token': token,
}

# Fetch data from the API
def fetch_data():
    response = requests.get('https://metastats-api-v1.new-york.agiliumtrade.ai/users/current/accounts/28c98cc1-cc61-4220-8a39-e4896ad746a5/open-trades/', headers=headers)
    data = response.json()
    df = pd.DataFrame(data['openTrades'])
    return df

class MyApp(reflex.App):
    def __init__(self):
        super().__init__()
        self.data = fetch_data()
        self.timer = reflex.Timer(interval=10, callback=self.update_data)
        self.table = reflex.Table(data=self.data)

    def layout(self):
        return reflex.Container(children=[
            reflex.Row(children=[
                self.table
            ])
        ])

    def update_data(self):
        self.data = fetch_data()
        self.table.data = self.data

if __name__ == "__main__":
    MyApp().run()