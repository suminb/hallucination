__author__ = 'Sumin Byeon'
__version__ = '0.1.1'

from sqlalchemy import MetaData
from sqlalchemy.sql import func
from core import app, db
from models import *

import logging

logger = logging.getLogger('hallucination')
logger.addHandler(logging.FileHandler('frontend.log')) 
logger.setLevel(logging.INFO)

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
    """Imports a list of proxy servers from a text file."""
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
                    logger.error(e)
                    db.session.rollback()


def export_proxies():
    """Exports the list of proxy servers to the standard output."""
    for row in Proxy.query.all():
        print '%s://%s:%d' % (row.protocol, row.host, row.port)


def select(n):
    """Randomly selects ``n`` proxy records. If ``n`` is 1, it returns a single
    object. It returns a list of objects otherwise.

    NOTE: Currently the value of ``n`` is being ignored.
    """

    if n <= 0:
        raise Exception('n must be a positive integer.')

    if n > Proxy.query.count():
        raise Exception('Not enough proxy records.')

    record = db.session \
            .query(AccessRecord.proxy_id, func.avg(AccessRecord.access_time).label('avg_access_time')) \
            .group_by(AccessRecord.proxy_id) \
            .order_by('avg_access_time') \
            .first()

    if record != None:
        return Proxy.query.get(record.proxy_id)
    else:
        # FIXME: What happens if there is no proxy record?
        return Proxy.query.first()

    #rows = Proxy.query.limit(n)
    # if n == 1:
    #     return rows.first()
    # else:
    #     return rows.all()


def report(id, status):
    pass


def make_request(url, headers=[], params=[], timeout=config.DEFAULT_TIMEOUT):
    """Fetches a URL via a automatically selected proxy server, then reports the status."""

    from datetime import datetime
    from requests.exceptions import ConnectionError, Timeout
    import requests
    import time

    proxy_server = select(1)
    #proxy_server = get(10)
    logger.info('%s has been selected.' % proxy_server)

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
        logger.error(e)

    except Timeout as e:
        logger.error(e)

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
    #import_proxies('proxylist.txt')
    r = make_request('http://stackoverflow.com/questions/1052148/group-by-count-function-in-sqlalchemy')
    print r.text