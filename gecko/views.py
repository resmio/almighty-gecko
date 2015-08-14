from datetime import date, timedelta

from flask import Flask
from flask_geckoboard import Geckoboard
import numpy as np

from query_db import run_query

app = Flask(__name__)
geckoboard = Geckoboard(app)


@app.route('/active_verified_facilities')
@geckoboard.line_chart
def active_verified_facilities():
    df = run_query('bookings_and_facilities')
    bookings = df[df.created.notnull()]
    bookings.created = bookings.created.apply(lambda d: d.date())
    df.f_created = df.f_created.apply(lambda d: d.date())
    current_date = date.today()
    end_date = date(day=1, month=1, year=2015)
    delta = timedelta(days=7)
    actives = []
    verifieds = []
    dates = []
    while current_date >= end_date:
        dates.append('{}'.format(current_date))
        actives.append(len(bookings[
            (bookings.created <= current_date) &
            (bookings.created >
             (current_date - timedelta(days=30)))].facility_id.unique()))
        verifieds.append(
            len(df[df.f_created <= current_date].facility_id.unique()))
        current_date -= delta
    return {'series': [{'data': actives[::-1], 'name': 'Active'},
                       {'data': verifieds[::-1], 'name': 'Verified'}],
            'x_axis': {'labels': dates[::-1], 'type': 'datetime'}}


@app.route('/new_lost_active_facilities')
@geckoboard.line_chart
def new_lost_active_facilities():
    bookings = run_query('bookings')
    bookings.created = bookings.created.apply(lambda d: d.date())
    today = date.today().toordinal()
    # Get the last sunday
    current_date = date.fromordinal(today - (today % 7))
    end_date = date(day=1, month=1, year=2015)
    delta = timedelta(days=7)
    dates = []
    active = []
    deactive = []
    reactive = []
    while current_date >= end_date:
        dates.append('{}'.format(current_date))
        this_month = set(bookings[
            (bookings.created <= current_date) &
            (bookings.created >= (current_date - timedelta(days=30)))]
            .facility_id.unique())
        last_month = set(bookings[
            (bookings.created >= (current_date - timedelta(days=60))) &
            (bookings.created < (current_date - timedelta(days=30)))]
            .facility_id.unique())
        before = set(bookings[
            bookings.created <= (current_date - timedelta(days=60))]
            .facility_id.unique())
        active.append(len(this_month.difference(
            last_month.union(before))))
        deactive.append(len(last_month.difference(this_month)))
        reactive.append(len(before.difference(
            last_month).intersection(this_month)))
        current_date -= delta
    return {'series': [{'data': active[::-1], 'name': 'Activated'},
                       {'data': deactive[::-1], 'name': 'De-activated'},
                       {'data': reactive[::-1], 'name': 'Re-activated'}],
            'x_axis': {'labels': dates[::-1], 'type': 'datetime'}}


@app.route('/current_active_numbers')
@geckoboard.rag
def current_active_numbers():
    bookings = run_query('bookings')
    bookings.created = bookings.created.apply(lambda d: d.date())
    # Get the last sunday
    today = date.today().toordinal()
    current_date = date.fromordinal(today - (today % 7))
    this_month = set(bookings[
        (bookings.created <= current_date) &
        (bookings.created >= (current_date - timedelta(days=30)))]
        .facility_id.unique())
    last_month = set(bookings[
        (bookings.created >= (current_date - timedelta(days=60))) &
        (bookings.created < (current_date - timedelta(days=30)))]
        .facility_id.unique())
    before = set(bookings[
        bookings.created <= (current_date - timedelta(days=60))]
        .facility_id.unique())
    activated = len(this_month.difference(
        last_month.union(before)))
    deactivated = len(last_month.difference(this_month))
    reactivated = len(before.difference(
        last_month).intersection(this_month))
    return ((deactivated, "De-activated"),
            (reactivated, "Re-activated"),
            (activated, "Activated"))


@app.route('/most_active_free_plan')
@geckoboard.leaderboard
def most_active_free_plan():
    bookings = run_query('bookings_with_subscription')
    free_plans = ['flex', 'flex_legacy', '2014-11-free']
    bookings = bookings[bookings.subscription_type.isin(free_plans)]
    bookings.created = bookings.created.apply(lambda d: d.date())
    # Get the last sunday
    today = date.today().toordinal()
    current_date = date.fromordinal(today - (today % 7))
    top20_this_week = bookings[
        (bookings.created <= current_date) &
        (bookings.created >= (
            current_date - timedelta(days=30)))].facility_id.value_counts(
                ascending=False).head(20)
    current_date -= timedelta(days=7)
    values_last_week = bookings[
        (bookings.created <= current_date) &
        (bookings.created >=
         (current_date - timedelta(days=30)))].facility_id.value_counts(
             ascending=False)
    previous_ranks = [int(np.where(values_last_week.index == f)[0] + 1)
                      for f in top20_this_week.index]
    return (top20_this_week.index, top20_this_week.values, previous_ranks)
