from datetime import datetime
import random
import re
import sys
import time

import logging
import requests
from requests.exceptions import ConnectionError, Timeout
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from hallucination.models import AccessRecord, Base, Proxy


class ProxyFactory:
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
        """Randomly selects ``n`` proxy records. If ``n`` is 1, it returns a single
        object. It returns a list of objects otherwise.

        :param protocols: Request endpoint protocol (http, https)
        """

        if n <= 0:
            raise ValueError("n must be a positive integer.")

        if n > self.session.query(Proxy).count():
            raise Exception("Not enough proxy servers.")

        # statement = '''
        #     SELECT *, avg(access_time) AS avg_access_time FROM (
        #         SELECT *, (-10*alive)+access_time FROM access_record ORDER BY access_time, "timestamp" DESC LIMIT :n
        #     ) GROUP BY proxy_id ORDER BY avg_access_time
        # '''

        statement = """
            SELECT * FROM proxy AS p LEFT JOIN (
                SELECT proxy_id, avg(latency) AS avg_latency, avg(alive) AS hit_ratio
                    FROM (SELECT * FROM access_record ORDER BY created_at DESC LIMIT 2500) AS t1
                    GROUP BY proxy_id
                ) AS ar ON p.rowid = ar.proxy_id
                WHERE p.protocol IN :protocols
                ORDER BY ar.hit_ratio DESC, ar.avg_latency
                LIMIT :n
        """

        # timestamp = datetime.utcnow() - timedelta(hours=1)

        record = (
            self.session.query(Proxy)
            .from_statement(text(statement))
            .params(protocols=tuple(protocols), n=n)
            .all()
        )

        return record

        # if record != None:
        #     return self.session.query(Proxy).filter_by(id=record.proxy_id).first()
        # else:
        #     return self.session.query(Proxy).order_by(func.random()).first()
        #     #raise Exception('No available proxy found.')

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

        if proxy is None:
            proxy = random.choice(self.select(pool_size).all())
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

        except Timeout as e:
            self.logger.error(e)

        except Exception as e:
            self.logger.exception(e)

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

            try:
                self.session.add(record)
                self.session.commit()
            except Exception as e:
                self.logger.exception(e)
                self.session.rollback()

            if r is not None:
                self.logger.debug("Response body: %s" % r.text)

        return r
