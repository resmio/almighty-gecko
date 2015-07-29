from datetime import date, timedelta

import pandas as pd
from flask import Flask
from flask_geckoboard import Geckoboard

from query_db import run_query

app = Flask(__name__)
geckoboard = Geckoboard(app)


@app.route('/number_facilities')
@geckoboard.number
def number_facilities():
    fname = run_query('facilities')
    facilities = pd.read_csv(fname)
    last_month = facilities[
        facilities.date_created < (
            date.today() - timedelta(days=30))].id.count()
    this_month = facilities.id.count()
    return (this_month, last_month)
