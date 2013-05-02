from sqlalchemy import MetaData
from core import app, db
from models import *

import logging


def create_db():
    db.create_all()


def get(id):
    return Proxy.query.get(id)


def insert(protocol, host, port):
    """Inserts a proxy record into the database. Returns an ID of the newly created object."""

    p = Proxy(protocol=protocol, host=host, port=port)

    db.session.add(p)
    db.session.commit()

    return p.id


def update(id, **pairs):
    pass


def delete(id):
    pass


def import_proxies(file_name):
    import re

    with open(file_name) as f:
        for line in f.readlines():
            # FIXME: This is an incomplete pattern matching
            match = re.match(r'(\w+)://([a-zA-Z0-9_.]+):(\d+)', line)

            if match != None:
                protocol, host, port = match.group(1), match.group(2), int(match.group(3))

                logging.info('Insert: %s' % line)

                proxy = Proxy(protocol=protocol, host=host, port=port)

                try:
                    db.session.add(proxy)
                    db.session.commit()
                except Exception as e:
                    logging.error(e)
                    db.session.rollback()


def export_proxies():
    for row in Proxy.query.all():
        print '%s://%s:%d' % (row.protocol, row.host, row.port)


def select(n):
    """Randomly selects ``n`` proxy records. If ``n`` is 1, it returns a single
    object. It returns a list of objects otherwise."""

    if n <= 0:
        raise Exception('n must be a positive integer.')

    if n > Proxy.query.count():
        raise Exception('Not enough proxy records.')

    rows = Proxy.query.limit(n)
    if n == 1:
        return rows.first()
    else:
        return rows.all()


def report(id, status):
    pass


def make_request(url, headers=[], params=[], timeout=config.DEFAULT_TIMEOUT):
    """Fetches a URL via a automatically selected proxy server, then reports the status."""

    from datetime import datetime
    from requests.exceptions import ConnectionError, Timeout
    import requests
    import time

    #proxy_server = select(1)
    proxy_server = get(1)

    proxy_dict = {'http': '%s:%d' % (proxy_server.host, proxy_server.port)}

    start_time = time.time()

    alive = False
    status_code = None
    try:
        # TODO: Support for other HTTP verbs
        r = requests.get(url, headers=headers, proxies=proxy_dict, timeout=timeout)
        alive = True
        status_code = r.status_code

    except ConnectionError as e:
        logging.error(e)

    except Timeout as e:
        logging.error(e)

    end_time = time.time()

    record = AccessRecord(
        proxy_id=proxy_server.id,
        timestamp=datetime.now(),
        alive=alive,
        url=url,
        access_time=end_time-start_time,
        status_code=status_code)

    db.session.add(record)
    db.session.commit()

    return r

if __name__ == '__main__':
    #create_db()
    #print insert('http', '118.145.3.44', '81')
    #r = make_request('http://blog.suminbbb.com')
    #print r.text.encode('utf-8')

    import_proxies('proxylist.txt')