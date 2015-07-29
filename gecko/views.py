from datetime import date, timedelta

from flask import Flask
from flask_geckoboard import Geckoboard

from query_db import run_query

app = Flask(__name__)
geckoboard = Geckoboard(app)


@app.route('/number_facilities')
@geckoboard.number
def number_facilities():
    facilities = run_query('facilities')
    facilities['date_created'] = map(lambda d: d.date(),
                                     facilities.created)
    last_month = facilities[
        facilities.date_created < (
            date.today() - timedelta(days=30))].id.count()
    this_month = facilities.id.count()
    return (this_month, last_month)
