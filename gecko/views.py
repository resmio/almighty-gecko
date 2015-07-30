from datetime import date, timedelta

from flask import Flask
from flask_geckoboard import Geckoboard

from query_db import run_query

app = Flask(__name__)
geckoboard = Geckoboard(app)


@app.route('/number_facilities')
@geckoboard.number
def number_facilities():
    facilities = run_query('number_facilities')
    facilities.created = facilities.created.apply(lambda d: d.date())
    last_month = facilities[
        facilities.created < (date.today() - timedelta(days=30))].id.count()
    this_month = facilities.id.count()
    return (this_month, last_month)


@app.route('/number_bookings')
@geckoboard.number
def number_bookings():
    bookings = run_query('number_bookings')
    bookings.created = bookings.created.apply(lambda d: d.date())
    last_month = bookings[
        bookings.created < (date.today() - timedelta(days=30))].created.count()
    this_month = bookings.created.count()
    return (this_month, last_month)


@app.route('/active_facilities')
@geckoboard.line_chart
def active_facilities():
    bookings = run_query('active_facilities')
    bookings.created = bookings.created.apply(lambda d: d.date())
    current_date = date.today()
    end_date = date(day=1, month=1, year=2015)
    delta = timedelta(days=7)
    actives = []
    dates = []
    while current_date >= end_date:
        dates.append('{}'.format(current_date))
        actives.append(len(bookings[
            (bookings.created <= current_date) &
            (bookings.created >
             (current_date - timedelta(days=30)))].facility_id.unique()))
        current_date -= delta
    return {'series': [{'data': actives[::-1], 'name': 'Active'}],
            'x_axis': {'labels': dates[::-1], 'type': 'datetime'}}
