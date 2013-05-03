from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.ext.declarative import DeclarativeMeta
#from sqlalchemy.dialects.postgresql import UUID
from core import app, db

import logging
import config


def serialize(obj):
    import json
    if isinstance(obj.__class__, DeclarativeMeta):
        # an SQLAlchemy class
        fields = {}
        for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata']:
            data = obj.__getattribute__(field)
            try:
                json.dumps(data) # this will fail on non-encodable values, like other classes
                fields[field] = data
            except TypeError:
                fields[field] = None
        # a json-encodable dict
        return fields


class Proxy(db.Model):
    """
    In SQLite, every row of every table has an 64-bit signed integer ROWID.
    The ROWID for each row is unique among all rows in the same table.

    You can access the ROWID of an SQLite table using one the special column
    names ROWID, _ROWID_, or OID. Except if you declare an ordinary table column
    to use one of those special names, then the use of that name will refer to
    the declared column not to the internal ROWID.

    See http://sqlite.org/autoinc.html for more details.

    """

    __table_args__ = (UniqueConstraint('protocol', 'host', 'port'),)

    id = db.Column('ROWID', db.Integer, primary_key=True)
    protocol = db.Column(db.String(8))
    host = db.Column(db.String(255))
    port = db.Column(db.Integer)

    hit_ratio = db.Column(db.Float(precision=64)) # aggregated value
    access_time = db.Column(db.Float(precision=64)) # aggregated average value
    last_updated = db.Column(db.DateTime(timezone=True)) # aggregated average value

    def __repr__(self):
        return 'Proxy %s://%s:%d' % (self.protocol, self.host, self.port)

    def serialize(self):
        return serialize(self)

    def test_reference_page(self, timeout=config.DEFAULT_TIMEOUT):
        """Tests if the proxy server returns an HTTP 200 message and a correct content
        when trying to access a reference page."""

        import random
        import requests

        proxy_dict = {'http': '%s:%d' % (self.host, self.port)}
        random_key = random.randint(0, 100000000)
        url = 'http://static.suminb.com/ref.php?key=%d' % random_key

        try:
            r = requests.get(url, proxies=proxy_dict, timeout=timeout)

            if r.status_code == 200 and r.text.strip() == str(random_key):
                return True

        except Exception as e:
            logging.error(e)

        return False

    def test_nonexisting_page(self, timeout=config.DEFAULT_TIMEOUT):
        """Tests if the proxy server returns an HTTP 404 message when trying to access a
        non-existing page."""

        import requests

        proxy_dict = {'http': '%s:%d' % (self.host, self.port)}
        url = 'http://static.suminb.com/nonexisting'

        try:
            r = requests.get(url, proxies=proxy_dict, timeout=timeout)

            if r.status_code == 404:
                return True

        except Exception as e:
            logging.error(e)

        return False

    def test_nonexisting_domain(self, timeout=config.DEFAULT_TIMEOUT):
        """Tests if the proxy server times-out when trying to access a non-existing domain."""

        import requests

        proxy_dict = {'http': '%s:%d' % (self.host, self.port)}
        url = 'http://nonexisting.suminb.com'

        try:
            r = requests.get(url, proxies=proxy_dict, timeout=timeout)

            # Should not reach here unless the proxy is lying.
            return False

        except Exception as e:
            logging.error(e)

        return True

    def fetch_url(self, url, headers=[], params=[]):

        import requests
        import proxybank

        proxy_dict = {self.protocol: '%s:%d' % (self.host, self.port)}

        req = requests.get(url, headers=headers, proxies=proxy_dict, timeout=proxybank.config.DEFAULT_TIMEOUT)
        #alive = True
        #status_code = r.status_code

        return req

class AccessRecord(db.Model):
    id = db.Column('ROWID', db.Integer, primary_key=True)
    proxy_id = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime(timezone=True))

    user_agent = db.Column(db.String(255))
    remote_address = db.Column(db.String(64))
    
    alive = db.Column(db.Boolean)
    url = db.Column(db.String(255))
    status_code = db.Column(db.Integer)
    access_time = db.Column(db.Float(precision=64))

    def serialize(self):
        return serialize(self)
