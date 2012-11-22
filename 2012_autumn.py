#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This program is free software. It comes without any warranty, to
# the extent permitted by applicable law. You can redistribute it
# and/or modify it under the terms of the Do What The Fuck You Want
# To Public License, Version 2, as published by Sam Hocevar. See
# http://sam.zoy.org/wtfpl/COPYING for more details.

from datetime import datetime
import logging
import re
import signal
import sqlite3
import urllib2

from lxml import html
from pyquery import PyQuery

import tweepy
from apscheduler.scheduler import Scheduler

import config

HASH_TAG = u'#Steam가을세일'

def timestamp_now():
    return int(datetime.now().strftime('%s'))

def parse_time_from_script(script_content):
    return int(script_re.search(script_content).group(1))

def parse_detail_link(link):
    m = link_re.match(link)
    if m is None:
        logging.warn('Invalid link: %s' % (link))
        raise LookupError
    return {'kind': m.group(1), 'id': int(m.group(2))}

def parse_app(app):
    app_link = app.children('a')
    if app_link.length == 0:
        logging.info('There is no link to an app or sub. It seems to be an empty space.')
        raise LookupError
    dc_div = app.find('.price')
    price_span = dc_div.children('span')

    try:
        ret = dict(parse_detail_link(app_link.attr.href))
    except LookupError as e:
        raise LookupError(e)
    ret['name'] = app_link.attr.title
    ret['discount'] = int(app.find('.percent').text().strip()[1:-1])
    ret['before_price'] = price_span.eq(0).text().strip()
    ret['now_price'] = price_span.eq(1).text().strip()
    ret['end_date'] = parse_time_from_script(app.find('script').text())
    return ret

def post_tweet(msg):
    if not first_run:
        try:
            api.update_status(msg)
        except tweepy.error.TweepError as e:
            logging.warn('Error while posting tweet: ' + str(e))
            logging.warn('The content of tweet was: ' + msg)

def fetch_flash_sale(pq):
    apps = pq('#flash_sales .item')
    for app in apps:
        try:
            parsed_app = parse_app(pq(app))
        except LookupError as e:
            continue

        cur.execute('SELECT COUNT(id) FROM flash_sale WHERE id = ?', (parsed_app['id'], ))
        if cur.fetchone()[0] > 0:
            logging.info('%d is already registered.' % (parsed_app['id']))
            continue

        logging.info('Newly registering app id %d.' % (parsed_app['id']))
        end_datetime = datetime.fromtimestamp(parsed_app['end_date'])
        post_tweet(HASH_TAG + u' 새로운 깜짝 할인: %(name)s %(before_price)s -%(discount)d%%-> %(now_price)s http://store.steampowered.com/%(kind)s/%(id)d/' % (parsed_app) + u' %d일 %d시 %d분까지' % (end_datetime.day, end_datetime.hour, end_datetime.minute))
        cur.execute('INSERT INTO flash_sale VALUES (:id, :kind, :name, :discount, :before_price, :now_price, :end_date)', parsed_app)

    conn.commit()

def do_job():
    try:
        f = urllib2.urlopen('http://store.steampowered.com/?cc=%s' % (config.COUNTRY_CODE))
    except urllib2.URLError as e:
        logging.warn(e)
        return
    parser = html.parse(f, html.HTMLParser(encoding='utf-8'))
    pq = PyQuery(parser.getroot())
    fetch_flash_sale(pq)

logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y/%m/%d %H:%M:%S')

conn = sqlite3.connect('2012_autumn.db', check_same_thread=False)
cur = conn.cursor()
sql_f = open('schema.sql')
cur.executescript(sql_f.read())

auth = tweepy.OAuthHandler(config.CONSUMER_KEY, config.CONSUMER_SECRET)
auth.set_access_token(config.ACCESS_TOKEN, config.ACCESS_TOKEN_SECRET)
api = tweepy.API(auth)

script_re = re.compile("InitDailyDealTimer\( \$\('\w+'\), ([0-9]+) \);")
link_re = re.compile('http:\/\/store\.steampowered\.com\/(app|sub)\/([0-9]+)')

sched = Scheduler()
sched.add_interval_job(do_job, minutes=2)
try:
    first_run = True
    do_job()
    first_run = False
    sched.start()
    signal.pause()
except KeyboardInterrupt:
    sched.shutdown()
    conn.close()