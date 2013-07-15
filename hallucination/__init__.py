__author__ = 'Sumin Byeon'
__version__ = '0.2.0'

from sqlalchemy import MetaData, create_engine
from sqlalchemy.sql.expression import func, select
from sqlalchemy.orm import sessionmaker
from models import *

import logging
import os, sys
import requests

logger = logging.getLogger('hallucination')
logger.addHandler(logging.FileHandler('frontend.log')) 
logger.setLevel(logging.INFO)

class Hallucination:

    def __init__(self, config={}):
        if not 'default_timeout' in config:
            config['default_timeout'] = 8

        self.config = config

        self.engine = create_engine(config['db_uri'])
        self.db = self.engine.connect()

        Session = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.session = Session()

    def create_db():
        db.create_all()


    def get(id):
        return Proxy.query.get(id)


    def insert(protocol, host, port):
        """Inserts a proxy record into the database. Returns an ID of the newly created object."""

        p = Proxy(protocol=protocol, host=host, port=port)

        self.session.add(p)
        self.session.commit()

        return p.id


    def update(id, **pairs):
        pass


    def delete(id):
        pass


    def import_proxies(self, file_name):
        """Imports a list of proxy servers from a text file."""
        import re

        with open(file_name) as f:
            for line in f.readlines():
                # FIXME: This is an incomplete pattern matching
                match = re.match(r'(\w+)://([a-zA-Z0-9_.]+):(\d+)', line)

                if match != None:
                    protocol, host, port = match.group(1), match.group(2), int(match.group(3))

                    logger.info('Insert: %s' % line)

                    proxy = Proxy(protocol=protocol, host=host, port=port)

                    try:
                        self.session.add(proxy)
                        self.session.commit()

                    except Exception as e:
                        logger.error(e)
                        self.session.rollback()


    def export_proxies(out=sys.stdout):
        """Exports the list of proxy servers to the standard output."""
        for row in Proxy.query.all():
            out.write('%s://%s:%d\n' % (row.protocol, row.host, row.port))


    def select(self, n):
        """Randomly selects ``n`` proxy records. If ``n`` is 1, it returns a single
        object. It returns a list of objects otherwise.

        NOTE: Currently the value of ``n`` is being ignored.
        """

        if n <= 0:
            raise Exception('n must be a positive integer.')

        if n > self.session.query(Proxy).count():
            raise Exception('Not enough proxy records.')

        record = self.session \
                .query(AccessRecord.proxy_id, func.avg(AccessRecord.access_time).label('avg_access_time')) \
                .group_by(AccessRecord.proxy_id) \
                .order_by('avg_access_time') \
                .first()

        # if record != None:
        #     logger.info('Access record found.')
        #     return self.session.query(Proxy).get(record.proxy_id)
        # else:
        #     # FIXME: What happens if there is no proxy record?
        #     logger.info('No access record found.')
        return self.session.query(Proxy).order_by(func.random()).first()


    def report(self, id, status):
        pass


    def make_request(self, url, headers=[], params=[], timeout=0, req_type=requests.get):
        """Fetches a URL via a automatically selected proxy server, then reports the status."""

        from datetime import datetime
        from requests.exceptions import ConnectionError, Timeout
        import time

        proxy_server = self.select(1)
        #proxy_server = get(10)
        logger.info('%s has been selected.' % proxy_server)

        proxy_dict = {'http': '%s:%d' % (proxy_server.host, proxy_server.port)}

        start_time = time.time()

        alive = False
        try:
            if timeout == 0:
                timeout = self.config['default_timeout']

            # TODO: Support for other HTTP verbs
            #r = requests.get(url, headers=headers, proxies=proxy_dict, timeout=timeout)
            r = req_type(url, headers=headers, data=params, proxies=proxy_dict, timeout=timeout)
            alive = True
            status_code = r.status_code if r != None else 0

            end_time = time.time()

            record = AccessRecord(
                proxy_id=proxy_server.id,
                timestamp=datetime.now(),
                alive=alive,
                url=url,
                access_time=end_time-start_time,
                status_code=status_code)

            logger.info('Access record: %s' % record)

            self.session.add(record)
            self.session.commit()

            logger.debug('Response body: %s' % r.text)

            return r

        except ConnectionError as e:
            logger.error(e)
            raise e

        except Timeout as e:
            logger.error(e)
            raise e

