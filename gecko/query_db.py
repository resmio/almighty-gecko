from datetime import date
from flatdict import FlatDict
from intercom import Company, Intercom
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


def run_query(query_key):
    """ Run a query on the resmio database and return the result as
        a pandas DataFrame. Queries can be specified in the dictionary in
        ``queries.py``.

    """
    return pd.read_sql_query(QUERIES[query_key], conn)


def intercom_companies():
    """ Get all companies from Intercom and return the data as a pandas
        DataFrame.

    """
    Intercom.app_id = get_config('INTERCOM_APP_ID')
    Intercom.app_api_key = get_config('INTERCOM_API_KEY')
    company_list = [FlatDict(c.to_dict) for c in Company.all()
                    if c.custom_attributes['Verified']]
    companies = []
    for c in company_list:
        dic = {}
        for k, v in c.iteritems():
            kn = k.lower().split(':')[-1].replace(' ', '_')
            dic[kn] = v
        companies.append(dic)
    companies = pd.DataFrame(companies)
    companies = companies.T.drop(
        ['0', '1', 'id', 'widget_integrated', 'app_id',
         'automatic_confirm_bookings', 'minimum_book_in_advance_hours',
         'phone_number', 'monthly_spend']).T
    companies.last_request_at = companies.last_request_at.apply(
        lambda x: date.fromtimestamp(x))
    companies.created_at = companies.created_at.apply(
        lambda x: date.fromtimestamp(x))
    companies.remote_created_at = companies.remote_created_at.apply(
        lambda x: date.fromtimestamp(x))
    companies.updated_at = companies.updated_at.apply(
        lambda x: date.fromtimestamp(x))
    return companies
