from datetime import date, timedelta
import os

from flask import Flask
from flask.ext.cache import Cache
from flask_geckoboard import Geckoboard
import numpy as np
import pandas as pd
import github3

from ga import get_ga_reader
from query_db import intercom_companies, run_query

app = Flask(__name__)

if 'CONFIG_SETTINGS' in os.environ:
    app.config.from_object(os.environ['CONFIG_SETTINGS'])
else:
    app.config.from_object('config.DevelopmentConfig')

cache = Cache(app)
geckoboard = Geckoboard(app)


@app.route('/active_verified_facilities')
@cache.cached(timeout=300)
@geckoboard.line_chart
def active_verified_facilities():
    """ Line chart with the weekly number of verified and active facilities. """
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
@cache.cached(timeout=300)
@geckoboard.line_chart
def new_lost_active_facilities():
    """ Weekly number of activated, de-activated, and re-activated facilities.

    """
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
@cache.cached(timeout=300)
@geckoboard.rag
def current_active_numbers():
    """ Current number of actived, de-activated, and re-activated facilities.

    """
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
@cache.cached(timeout=300)
@geckoboard.leaderboard
def most_active_free_plan():
    """ Leaderboard with the most active facilities (in the last month) on a
        free plan.

    """
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
                ascending=False).head(22)
    current_date -= timedelta(days=7)
    values_last_week = bookings[
        (bookings.created <= current_date) &
        (bookings.created >=
         (current_date - timedelta(days=30)))].facility_id.value_counts(
             ascending=False)
    previous_ranks = [int(np.where(values_last_week.index == f)[0] + 1)
                      for f in top20_this_week.index]
    return (top20_this_week.index, top20_this_week.values, previous_ranks)


@app.route('/least_active_paying')
@cache.cached(timeout=300)
@geckoboard.leaderboard
def least_active_paying():
    """ Leaderboard with the least active facilities on a payed plan. """
    bookings = run_query('bookings_with_subscription')
    facilities = run_query('facilities_with_subscription')
    free_plans = ['flex', 'flex_legacy', '2014-11-free', 'basic', 'custom']

    # Get the last sunday
    today = date.today().toordinal()
    current_date = date.fromordinal(today - (today % 7))

    # Get all paying facilities with plans created at least 3 months ago
    facilities = facilities[~facilities.subscription_type.isin(free_plans)]
    facilities = facilities[
        facilities.begins <= (current_date - timedelta(days=90))]
    facilities = facilities[facilities.ends.isnull()]

    # Get all bookings from paying facilities created at least 3 months ago
    bookings = bookings[~bookings.subscription_type.isin(free_plans)]
    bookings = bookings[bookings.s_begin <= (current_date - timedelta(days=90))]
    bookings.created = bookings.created.apply(lambda d: d.date())

    least_bookings = bookings[
        (bookings.created <= current_date) &
        (bookings.created >= (
            current_date - timedelta(days=30)))].facility_id.value_counts(
                ascending=True)

    # Get facilities without bookings (not in bottom_this_week)
    no_bookings = set(facilities.id.values).difference(
        set(least_bookings.index))

    # Bottom 22 facilities
    bottom = pd.Series(0, index=no_bookings).append(least_bookings).head(22)

    labels = ['{} ({})'.format(
        f, facilities[facilities.id == f]['subscription_type'].values[-1])
        for f in bottom.index]

    return (labels, bottom.values, np.arange(0, 22) + 1, 'ascending')


@app.route('/number_bookings')
@cache.cached(timeout=300)
@geckoboard.line_chart
def number_bookings():
    """ Weekly number of bookings. """
    bookings = run_query('bookings')
    bookings = bookings[bookings.source != '']
    bookings = bookings.set_index('created')
    bookings = bookings.loc['20150101':]
    bookings_count = bookings.facility_id.resample('w', how='count')
    bookings_count.index = map(lambda d: d.date(), bookings_count.index)
    dates = ['{}'.format(d) for d in bookings_count.index]
    return {'series': [{'data': bookings_count.values.tolist()[:-1],
                        'name': 'Bookings'}],
            'x_axis': {'labels': dates[:-1], 'type': 'datetime'}}


@app.route('/number_covers')
@cache.cached(timeout=300)
@geckoboard.line_chart
def number_covers():
    """ Weekly number of covers. """
    bookings = run_query('bookings')
    bookings = bookings[bookings.source != '']
    bookings = bookings.set_index('created')
    bookings = bookings.loc['20150101':]
    bookings_count = bookings.num.resample('w', how='sum')
    bookings_count.index = map(lambda d: d.date(), bookings_count.index)
    dates = ['{}'.format(d) for d in bookings_count.index]
    return {'series': [{'data': bookings_count.values.tolist()[:-1],
                        'name': 'Covers'}],
            'x_axis': {'labels': dates[:-1], 'type': 'datetime'}}


@app.route('/number_pages_bookings')
@cache.cached(timeout=300)
@geckoboard.line_chart
def number_pages_bookings():
    """ Weekly number of bookings through the landingpages. """
    bookings = run_query('bookings')
    bookings = bookings[bookings.source == 'pages.resmio.com']
    bookings = bookings.set_index('created')
    bookings = bookings.loc['20150101':]
    bookings_count = bookings.num.resample('w', how='count')
    bookings_count.index = map(lambda d: d.date(), bookings_count.index)
    dates = ['{}'.format(d) for d in bookings_count.index]
    return {'series': [{'data': bookings_count.values.tolist()[:-1],
                        'name': 'Bookings'}],
            'x_axis': {'labels': dates[:-1], 'type': 'datetime'}}


@app.route('/top_pages_facilities')
@cache.cached(timeout=300)
@geckoboard.leaderboard
def top_pages_facilities():
    """ Leaderboard of facilities with bookings through landingpages. """
    bookings = run_query('bookings')
    bookings = bookings[bookings.source == 'pages.resmio.com']
    bookings.created = bookings.created.apply(lambda x: x.date())
    bookings = bookings[bookings.created >=
                        (date.today() - timedelta(days=30))]
    bookings_count = bookings.facility_id.value_counts()
    return (bookings_count.index, bookings_count.values)


@app.route('/most_visited_app_urls')
@cache.cached(timeout=300)
@geckoboard.leaderboard
def most_visited_app_urls():
    """ List of most visited app views and the average time spent on each.

    """
    reader = get_ga_reader()
    account_id = app.config.get('GA_ACCOUNT_ID')
    property_id = app.config.get('GA_APP_PROPERY_ID')
    metrics = ['pageviews', 'avgTimeOnSite']
    dimensions = ['pagePathLevel2', 'pagePathLevel3']
    start_date = '2015-01-01'
    end_date = date.today()
    df = reader.get_data(metrics=metrics, dimensions=dimensions,
                         start_date=start_date, end_date=end_date,
                         account_id=account_id, property_id=property_id,
                         index_col=0)
    sorted_df = df.sort('pageviews', ascending=False)
    paths = map(lambda p1, p2: p1[:-1] + p2, sorted_df.index,
                sorted_df.pagePathLevel3)
    labels = map(lambda p, v: '{} (views: {})'.format(
        p.encode('ascii', 'ignore'), v), paths, sorted_df.pageviews)
    return (labels[:10], sorted_df.avgTimeOnSite.values[:10])


@app.route('/unique_widget_views')
@cache.cached(timeout=300)
@geckoboard.line_chart
def unique_widget_views():
    """ Number of unique widget views over time. """
    reader = get_ga_reader()
    account_id = app.config.get('GA_ACCOUNT_ID')
    property_id = app.config.get('GA_WIDGET_PROPERTY_ID')
    metrics = ['uniquePageviews']
    dimensions = ['date']
    start_date = '2015-01-01'
    end_date = date.today()
    df = reader.get_data(metrics=metrics, dimensions=dimensions,
                         start_date=start_date, end_date=end_date,
                         account_id=account_id, property_id=property_id,
                         index_col=0)
    widget_counts = df.uniquePageviews.resample('w', how='sum')
    dates = ['{}'.format(d.date()) for d in widget_counts.index]
    return {'series': [{'data': widget_counts.values.tolist()[:-1],
                        'name': 'Widget Views'}],
            'x_axis': {'labels': dates[:-1], 'type': 'datetime'}}


@app.route('/least_widget_views')
@cache.cached(timeout=300)
@geckoboard.leaderboard
def least_widget_views():
    facilities = run_query('facilities_with_subscription')
    companies = intercom_companies()
    free_plans = ['flex', 'flex_legacy', '2014-11-free', 'basic', 'custom']
    facilities.created = facilities.created.apply(lambda d: d.date())
    last_month = date.today() - timedelta(days=30)
    paying_facilities = facilities[
        ~facilities.subscription_type.isin(free_plans)
        & facilities.ends.isnull()
        & (facilities.created <= last_month)].id.tolist()
    paying_companies = companies[companies.company_id.isin(paying_facilities)]
    sorted_df = paying_companies.sort('number_of_unique_pageviews_last_month')
    labels = ['{} ({})'.format(f, facilities[
        facilities.id == f]['subscription_type'].values[-1])
        for f in sorted_df.company_id]
    return (labels[:22],
            sorted_df.number_of_unique_pageviews_last_month[:22]
            .values.astype(int),
            np.arange(0, 22) + 1,
            'ascending')


@app.route('/paying_least_bookings')
@cache.cached(timeout=300)
@geckoboard.leaderboard
def paying_least_bookings():
    """ Leaderboard with the least active facilities on a payed plan. """
    bookings = run_query('bookings')
    facilities = run_query('facilities_with_subscription')
    free_plans = ['flex', 'flex_legacy', '2014-11-free', 'basic', 'custom']

    bookings.created = bookings.created.apply(lambda d: d.date())

    # Get the last sunday
    today = date.today().toordinal()
    current_date = date.fromordinal(today - (today % 7))

    paying_facilities = facilities[
        ~facilities.subscription_type.isin(free_plans)]
    paying_facilities = paying_facilities[
        paying_facilities.begins <= (current_date - timedelta(days=60))]

    bookings_last_month = bookings[
        bookings.created >= current_date - timedelta(days=30)]
    b_counts = bookings_last_month.facility_id.value_counts()

    labels = []
    counts = []
    for f_id in paying_facilities.id:
        labels.append(f_id)
        if f_id in b_counts.index:
            counts.append(b_counts[f_id])
        else:
            counts.append(0)
    idx = np.argsort(counts)
    counts = np.asarray(counts)[idx][:22]
    labels = np.asarray(labels)[idx][:22]

    labels = ['{} ({})'.format(
        f, facilities[facilities.id == f]['subscription_type'].values[-1])
        for f in labels]
    return (labels, counts)


@app.route('/project_x_points')
@cache.cached(timeout=300)
@geckoboard.rag
def github_issues_project_x():
    GITHUB_TOKEN = app.config.get('GH_SECRET')
    ORG = 'resmio'
    REPOS = ['resmio', 'resmio-tables', 'hollow-butter', 'landingpages', ]

    SIZE_LUT = {
        'x-small': 1,
        'small': 2,
        'medium': 5,
        'large': 8,
        'x-large': 13,
    }

    gh = github3.login(token=GITHUB_TOKEN)

    open_points = 0
    all_points = 0

    for repo in REPOS:
        print 'checking "{}"'.format(repo)
        for i in gh.iter_repo_issues(ORG, repo, state='all'):
            issue = {
                'created_at': i.created_at,
                'closed_at': i.closed_at,
                'is_pull_request': (i.pull_request is not None),
                'labels': [l.name for l in i.labels],
                'repo': repo
            }
            issue_size = 0
            if 'Project X' in issue['labels']:
                for label in issue['labels']:
                    if label in SIZE_LUT:
                        issue_size += SIZE_LUT[label]
                all_points += issue_size
                if issue['closed_at'] is None:
                    open_points += issue_size

    return (
        (open_points, 'Open'),
        (all_points-open_points, 'Closed'),
    )
