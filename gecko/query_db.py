import psycopg2
from tempfile import NamedTemporaryFile
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
    cur = conn.cursor()
    output = 'COPY ({}) TO STDOUT WITH CSV HEADER'.format(query)
    f = NamedTemporaryFile(delete=False)
    cur.copy_expert(output, f)
    conn.close()
    f.close()
    return f.name


