import pg8000.native
import os
import time

DB_HOST = os.environ.get('DB_HOST', 'db-svc')
DB_USER = os.environ.get('POSTGRES_USER')
DB_PASS = os.environ.get('POSTGRES_PASSWORD')
DB_NAME = os.environ.get('POSTGRES_DB')

def get_connection():
    for _ in range(15):
        try:
            return pg8000.native.Connection(user=DB_USER, password=DB_PASS, database=DB_NAME, host=DB_HOST)
        except Exception:
            time.sleep(2)
    raise Exception("Database connection timeout.")