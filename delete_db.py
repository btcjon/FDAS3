import os
import sqlite3

# Delete the existing database file if it exists
if os.path.exists('positions.db'):
    os.remove('positions.db')

# SQLite connection
conn = sqlite3.connect('positions.db')