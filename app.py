#!/usr/bin/env python
# -*- coding: utf-8 -*-


import configparser
import io
import codecs
import csv
import logging
import os
import webbrowser
from collections import defaultdict

import click
from stravalib import unithelper
from stravalib.client import Client

LOG = logging.basicConfig(level=logging.ERROR)


class Row:

    def __init__(self, bikes, activity, this_effort=None, top_effort=None,
                 segment=None):
        self.bikes = bikes
        self.activity = activity
        self.this_effort = this_effort
        self.top_effort = top_effort
        self._segment = segment

    def id(self):
        return self._segment.id

    def bike(self):
        bike = self.bikes.get(self.activity.gear_id)
        if bike:
            return bike.name
        return '???'

    def ride_date(self):
        start = self.activity.start_date_local
        return start.strftime('%Y-%m-%d %H:%S')

    def ride_name(self):
        return self.activity.name

    def ride_distance(self):
        return '{0:0.3f}'.format(unithelper.miles(self.activity.distance).num)

    def ride_elapsed_time(self):
        return unithelper.seconds(self.activity.elapsed_time).num

    def ride_moving_time(self):
        return unithelper.seconds(self.activity.moving_time).num

    def name(self):
        return self._segment.name

    segment = name

    def starred(self):
        if self._segment.starred:
            return '*'
        else:
            return ''

    def distance(self):
        return '{0:0.3f}'.format(unithelper.miles(self._segment.distance).num)

    def time(self):
        return unithelper.seconds(self.this_effort.elapsed_time).num

    def pr(self):
        return unithelper.seconds(self.top_effort.elapsed_time).num

    def diff(self):
        diff = self.top_effort.elapsed_time.total_seconds() - \
               self.this_effort.elapsed_time.total_seconds()
        return unithelper.seconds(diff).num


class UTF8Recoder:
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """
    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode('utf-8')


class UnicodeReader:
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding='utf-8', **kwds):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.reader(f, dialect=dialect, **kwds)

    def next(self):
        row = self.reader.next()
        return [str(s, 'utf-8') for s in row]

    def __iter__(self):
        return self


class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding='utf-8', **kwds):
        # Redirect output to a queue
        self.queue = io.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        therow = []
        for s in row:
            if isinstance(s, str):
                therow.append(s.encode('utf-8'))
            else:
                therow.append(s)

        self.writer.writerow(therow)
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode('utf-8')
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


def get_auth_code(client, client_id):
    auth_url = 'http://localhost:8000/'
    authorize_url = client.authorization_url(client_id=client_id,
                                             redirect_uri=auth_url)
    webbrowser.open(authorize_url, True, True)


def get_bikes(athlete):
    d = dict()
    if hasattr(athlete, 'bikes'):
        for b in athlete.bikes:
            d[b.id] = b
    return d


def get_access_token():
    config = configparser.ConfigParser()
    config.read(['strava-pr.cfg',
                 os.path.expanduser('strava-pr.cfg'),
                 os.path.expanduser('.config/strava-pr/config')])
    client_id = config.get('strava-pr', 'CLIENT_ID')  # noqa
    # here is where we would get the access token if we didn't have it but we
    # do. :)
    access_token = config.get('strava-pr', 'ACCESS_TOKEN')
    return access_token


@click.group()
@click.pass_context
def main(ctx):
    client = Client()
    client.access_token = get_access_token()

    ctx.obj['client'] = client
    ctx.obj['athlete'] = client.get_athlete()

    ctx.obj['bikes'] = get_bikes(ctx.obj['athlete'])


@main.command(name='list')
@click.option('--limit', type=int)
@click.pass_context
def get_all_rides(ctx, limit):
    """List all the rides."""
    client = ctx.obj['client']
    bikes = ctx.obj['bikes']

    if limit:
        limit = int(limit)
    else:
        limit = None

    activities = client.get_activities(limit=limit)
    output = io.StringIO()
    csv_out = UnicodeWriter(output)
    columns = ['date', 'name', 'bikes', 'distance', 'elapsed_time',
               'moving_time']
    get_columns = ['ride_date', 'ride_name', 'bike', 'ride_distance',
                   'ride_elapsed_time', 'ride_moving_time']
    csv_out.writerow(columns)
    for a in activities:
        row = Row(bikes=bikes,
                  activity=a)
        out_row = []
        for f in get_columns:
            func = getattr(row, f)
            out_row.append(func())
        csv_out.writerow(out_row)
    print(output.getvalue().strip())


@main.command()
@click.pass_context
def summary(ctx):
    """Summary of everything you've done on Strava."""
    client = ctx.obj['client']
    bikes = ctx.obj['bikes']

    by_bike = defaultdict(lambda: defaultdict(int))

    activities = client.get_activities()
    for a in activities:
        if a.type != 'Ride':
            continue
        by_bike[a.gear_id]['distance'] += unithelper.miles(a.distance).num
        by_bike[a.gear_id]['rides'] += 1

    output = cStringIO.StringIO()
    csv_out = UnicodeWriter(output)
    columns = ['bike', 'rides', 'distance']
    csv_out.writerow(columns)
    for (bike, datap) in by_bike.items():
        bike_name = bikes.get(bike)
        if not bike_name:
            bike_name = 'Retired bike ({})'.format(bike)
        else:
            bike_name = bike_name.name
        csv_out.writerow([bike_name, datap['rides'],
                          '{0:0.2f}'.format(datap['distance'])])
    print(output.getvalue().strip())


@main.command()
@click.argument('rides', nargs=-1, type=int)
@click.pass_context
def ride(ctx, rides):
    """List all the segments from a ride."""
    client = ctx.obj['client']
    athlete = ctx.obj['athlete']
    bikes = ctx.obj['bikes']

    act_cache = dict()
    seg_cache = dict()

    if len(rides) == 1:
        activities = [client.get_activity(int(rides[0]),
                                          include_all_efforts=True)]
    elif len(rides) > 1:
        raise ValueError('Sorry, can only handle one ride at a time.')
    else:
        # get the most recent ride
        activities = client.get_activities(limit=1)

    output = cStringIO.StringIO()
    csv_out = UnicodeWriter(output)
    columns = ['id', 'name', 'starred', 'bike', 'distance',
               'time', 'pr', 'diff']
    csv_out.writerow(columns)
    for a in activities:
        if a.id not in act_cache and a.segment_efforts is None:
            a = client.get_activity(a.id, include_all_efforts=True)
        act_cache[a.id] = a
        efforts = a.segment_efforts
        for e in efforts:
            segment = seg_cache.get(e.segment.id, None) or \
                      client.get_segment(e.segment.id)
            seg_cache[e.segment.id] = segment

            top_efforts = client.get_segment_efforts(e.segment.id,
                                                     athlete_id=athlete.id,
                                                     limit=1)
            for tope in top_efforts:
                topa = act_cache.get(tope.activity.id, None)
                if not topa:
                    topa = act_cache.get(tope.activity.id, None) or \
                           client.get_activity(tope.activity.id)
                    act_cache[topa.id] = topa
                row = Row(bikes=bikes,
                          activity=topa,
                          this_effort=e,
                          top_effort=tope,
                          segment=segment)
                out_row = []
                for f in columns:
                    func = getattr(row, f)
                    out_row.append(func())
                csv_out.writerow(out_row)
        print(output.getvalue().strip())

if __name__ == '__main__':
    main(obj={})
