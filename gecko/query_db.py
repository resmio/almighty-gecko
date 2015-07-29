import pandas as pd
import psycopg2
import urlparse

from config import get_config
from queries import QUERIES

urlparse.uses_netloc.append('postgres')
url = urlparse.urlparse(get_config('RESMIO_DB_URL'))

conn = psycopg2.connect(
    database=url.path[1:],
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port)


def run_query(query_name):
    query_key = query_name
    query = QUERIES[query_key]
    return pd.read_sql_query(query, conn)
