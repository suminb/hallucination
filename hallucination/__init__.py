from datetime import datetime
import functools
import os
import random
import re
import sys
import time
from urllib.parse import urlparse

import logging
import requests
from requests.exceptions import ConnectionError, Timeout
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func

from hallucination.models import AccessRecord, Base, Proxy


# TODO: Perhaps we want to move this elsewhere
class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = \
                super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class ProxyFactory(metaclass=Singleton):
    # Why is this called 'factory'?

    def __init__(
        self,
        config={},
        db_engine=None,
        logger=logging.getLogger("hallucination"),
    ):
        self.config = config
        self.logger = logger

        if db_engine is None:
            self.engine = create_engine(config["db_uri"])
            self.db = self.engine.connect()
        else:
            self.engine = db_engine

        Session = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )
        self.session = Session()

        # NOTE: Workaround for AttributeError: 'Session' object has no
        # attribute '_model_changes'
        self.session._model_changes = dict()

    def __del__(self):
        self.close()

    def close(self):
        self.logger.info("Closing connections")
        if hasattr(self, "session") and self.session is not None:
            self.session.close()

        if hasattr(self, "db") and self.db is not None:
            self.db.close()

    def create_db(self):
        # Base class is from models module
        Base.metadata.create_all(self.engine)

    def get(self, id):
        return self.session.query(Proxy).get(id)

    def insert(self, protocol, host, port):
        """Inserts a proxy record into the database. Returns an ID of the
        newly created object.
        """

        p = Proxy(protocol=protocol, host=host, port=port)

        self.session.add(p)
        self.session.commit()

        return p.id

    def update(self, id, **pairs):
        pass

    def delete(self, id):
        pass

    def import_proxies(self, fin=sys.stdin):
        """Imports a list of proxy servers from a text file."""

        if type(fin) == str:
            res = None
            with open(fin) as f:
                res = self.import_proxies(f)
            return res

        self.logger.info("Importing proxy servers from %s" % fin)

        for line in fin.readlines():
            match = re.search(r"(\w+)://([a-zA-Z0-9_.]+):(\d+)", line)

            if match is not None:
                protocol, host, port = (
                    match.group(1),
                    match.group(2),
                    int(match.group(3)),
                )

                self.logger.info("Insert: %s://%s:%d" % (protocol, host, port))

                proxy = Proxy(protocol=protocol, host=host, port=port)

                try:
                    self.session.add(proxy)
                    self.session.commit()

                except Exception as e:
                    self.logger.error(e)
                    self.session.rollback()

    def export_proxies(self, out=sys.stdout):
        """Exports the list of proxy servers to the standard output."""
        for row in self.session.query(Proxy).all():
            out.write("%s://%s:%d\n" % (row.protocol, row.host, row.port))

    def select(self, protocols=["http", "https"], n=1):
        """Randomly selects ``n`` proxy records. If ``n`` is 1, it returns a
        single object. It returns a list of objects otherwise.

        :param protocols: Request endpoint protocol (http, https)
        """

        if n <= 0:
            raise ValueError("n must be a positive integer.")

        count = self.session.query(Proxy).count()
        if n > count:
            raise Exception("Not enough proxy servers.")

        return (
            self.session.query(Proxy)
            .filter(Proxy.protocol.in_(protocols))
            .order_by(Proxy.hit_ratio.desc(), Proxy.latency.desc())
            .offset(random.randint(0, (count - n) // 2))
            .limit(n)
            .all()
        )

    def get_evaluation_targets(self):
        statement = """
            SELECT * FROM proxy LEFT JOIN (
                SELECT proxy_id, count(*) AS count
                    FROM (SELECT * FROM access_record ORDER BY created_at DESC LIMIT 2500) AS t1
                    GROUP BY proxy_id
                ) AS ar ON proxy.rowid = ar.proxy_id
                WHERE ar.count IS NULL OR ar.count < 10
        """

        record = self.session.query(Proxy).from_statement(text(statement))

        return record

    def report(self, id, status):
        pass

    def make_request(
        self,
        url,
        headers=None,
        params=None,
        data=None,
        timeout=5,
        req_type=requests.get,
        proxy=None,
        pool_size=5,
    ):
        """Fetches a URL via a automatically selected proxy server, then
        reports the status.
        """

        parsed_url = urlparse(url)
        if proxy.protocol != parsed_url.scheme:
            raise ValueError(
                f"Proxy protocol ({proxy.protocol}) and "
                f"URL scheme ({parsed_url.scheme}) do not match"
            )

        if proxy is None:
            proxy = random.choice(
                self.select(n=pool_size, protocols=[parsed_url.scheme]).all()
            )
            self.logger.info(
                "No proxy is given. {0} has been selected.".format(proxy)
            )

        proxy_dict = {
            str(proxy.protocol): "{0}://{1}:{2}".format(
                proxy.protocol, proxy.host, proxy.port
            )
        }

        start_time = time.time()
        r = None
        exception = None
        alive = 0.0
        status_code = None
        try:
            if "timeout" in self.config:
                timeout = self.config["timeout"]

            r = req_type(
                url,
                headers=headers,
                params=params,
                data=data,
                proxies=proxy_dict,
                timeout=timeout,
            )

            status_code = r.status_code
            alive = 1.0 if status_code == 200 else -0.5

        except ConnectionError as e:
            self.logger.error(e)
            exception = e

        except Timeout as e:
            self.logger.error(e)
            exception = e

        except Exception as e:
            self.logger.exception(e)
            exception = e

        finally:
            end_time = time.time()

            record = AccessRecord(
                proxy_id=proxy.id,
                created_at=datetime.utcnow(),
                alive=alive,
                url=url,
                latency=end_time - start_time,
                status_code=status_code,
            )

            self.logger.info("Inserting access record: {0}".format(record))

            # Do not add `proxy` object to the current session. This will be
            # added by the main thread and updated by update_statistics()
            # later.
            proxy.updated_at = record.created_at

            try:
                self.session.add(record)
                self.session.commit()
            except Exception as e:
                self.logger.exception(e)
                self.session.rollback()
                exception = e

            if r is not None:
                self.logger.debug("Response body: %s" % r.text)

        if exception:
            raise exception
        else:
            return r

    def update_statistics(self, proxy):
        proxy.hit_ratio, proxy.latency = (
            self.session.query(
                func.avg(AccessRecord.alive), func.avg(AccessRecord.latency),
            )
            .filter(AccessRecord.proxy_id == proxy.id)
            .first()
        )

        try:
            self.session.add(proxy)
            self.session.commit()
        except Exception as e:
            self.logger.exception(e)
            self.session.rollback()


# 'Proxy' doesn't seem to be valid as a verb. Any better term?
def proxied_request(func):
    if "HALLUCINATION_DB_URI" not in os.environ:
        raise RuntimeError(
            "HALLUCINATION_DB_URI environment variable must be provided"
        )
    config = {"db_uri": os.environ.get("HALLUCINATION_DB_URI")}
    factory = ProxyFactory(config=config)

    @functools.wraps(func)
    def wrapper(url, *args, **kwargs):
        parsed_url = urlparse(url)
        [proxy] = factory.select([parsed_url.scheme], 1)
        try:
            resp = factory.make_request(
                url, *args, req_type=func, proxy=proxy, **kwargs
            )
        except Exception as e:
            factory.update_statistics(proxy)
            raise e
        return resp

    return wrapper
