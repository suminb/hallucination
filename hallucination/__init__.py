__author__ = 'Sumin Byeon'
__email__ = 'suminb@gmail.com'
__version__ = '0.2.1'

from sqlalchemy import MetaData, create_engine
from sqlalchemy.sql.expression import func, select
from sqlalchemy.orm import sessionmaker, aliased
from models import *
from datetime import datetime, timedelta

import logging
import os, sys
import requests

logger = logging.getLogger('hallucination')
logger.addHandler(logging.FileHandler('frontend.log')) 
logger.setLevel(logging.INFO)

class ProxyFactory:

    def __init__(self, config={}):
        if not 'default_timeout' in config:
            config['default_timeout'] = 5

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

        if n > self.session.query(AccessRecord).count():
            raise Exception('Not enough proxy records.')

        statement = '''
        SELECT * FROM (
            SELECT *, avg(access_time) AS avg_access_time, sum(status_code) AS sumsc, count(*) AS cnt FROM (
                    SELECT * FROM access_record WHERE timestamp > :timestamp
                ) GROUP BY proxy_id
        ) WHERE sumsc/cnt = 200 ORDER BY RANDOM()
        '''

        timestamp = datetime.now() - timedelta(hours=1)

        record = self.session.query(AccessRecord, 'proxy_id', 'avg_access_time').from_statement( \
            statement).params(timestamp=timestamp).first()

        if record != None:
            return self.session.query(Proxy).filter_by(id=record.proxy_id).first()
        else:
            raise Exception('No available proxy found.')


    def report(self, id, status):
        pass


    def make_request(self, url, headers=[], params=[], timeout=0, req_type=requests.get, proxy=None):
        """Fetches a URL via a automatically selected proxy server, then reports the status."""

        from datetime import datetime
        from requests.exceptions import ConnectionError, Timeout
        import time

        if proxy == None:
            proxy = self.select(1)
            logger.info('No proxy is given. %s has been selected.' % proxy)

        proxy_dict = {'http': '%s:%d' % (proxy.host, proxy.port)}

        start_time = time.time()
        r = None
        alive = False
        status_code = None
        try:
            if timeout == 0:
                timeout = self.config['default_timeout']

            # TODO: Support for other HTTP verbs
            #r = requests.get(url, headers=headers, proxies=proxy_dict, timeout=timeout)
            r = req_type(url, headers=headers, data=params, proxies=proxy_dict, timeout=timeout)
            alive = True
            status_code = r.status_code

        except ConnectionError as e:
            logger.error(e)
            raise e

        except Timeout as e:
            logger.error(e)
            raise e

        finally:
            end_time = time.time()

            record = AccessRecord(
                proxy_id=proxy.id,
                timestamp=datetime.now(),
                alive=alive,
                url=url,
                access_time=end_time-start_time,
                status_code=status_code)

            logger.info('Inserting access record: %s' % record)

            self.session.add(record)
            self.session.commit()

            if r != None: logger.debug('Response body: %s' % r.text)

        return r
