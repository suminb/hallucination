from hallucination import ProxyFactory
from hallucination.models import Proxy
from multiprocessing import Pool
from threading import Thread, Lock
from Queue import Queue

import getopt
import os, sys
import logging
import json

logger = logging.getLogger('hallucination')
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.INFO)

config = {}

# FIXME: This is not a good design
url = 'http://translate.google.com'
proxy_factory = None

threads = 8


class TestrunThread(Thread):
    def __init__(self, queue, config):
        super(TestrunThread, self).__init__()

        self.queue = queue

        self.proxy_factory = ProxyFactory(config=dict(
            db_uri=config['db_uri']),
            logger=logger
        )

    def run(self):
        while True:
            logger.info('Qsize = {} (approx.)'.format(self.queue.qsize()))

            url, proxy = self.queue.get()

            logger.info('Test run: Fetching %s via %s' % (url, proxy))
            self.proxy_factory.make_request(url, proxy=proxy, timeout=3)

            self.queue.task_done()


def create():
    proxy_factory.create_db()


def _import(file_path):
    """Imports a list of proxy servers from a text file."""
    proxy_factory.import_proxies(open(file_path, 'r'))


def export(file_path):
    """Exports the list of proxy servers to the standard output."""
    proxy_factory.export_proxies(open(file_path, 'w'))


def select():
    print proxy_factory.select(1)


def evaluate():
    """
    Selects proxy servers that have not been recently evaluated, and evaluates each of them.

    Refered http://docs.python.org/2/library/queue.html for skeleton code.
    """

    queue = Queue()

    for i in range(threads):
        thread = TestrunThread(queue=queue, config=config)
        thread.daemon = True
        thread.start()

    for proxy in proxy_factory.get_evaluation_targets():
        queue.put((url, proxy))

    queue.join()


def parse_config(file_name):
    raw_config = file(file_name, 'r').read()

    global config
    config = json.loads(raw_config)


def main():
    opts, args = getopt.getopt(sys.argv[1:], 'cti:x:sd:E', ['config='])

    rf = None
    params = []
    for o, a in opts:
        if o == '-c':
            rf = create
        elif o == '-t':
            rf = testrun
        elif o == '-i':
            rf = _import
            params = [a]
        elif o == '-x':
            rf = export
            params = [a]
        elif o == '-s':
            rf = select
        elif o == '-E':
            rf = evaluate

        elif o == '--config':
            parse_config(a)

        elif o == '-d':
            config['db_uri'] = 'sqlite:///%s' % a

    global proxy_factory
    proxy_factory = ProxyFactory(config=dict(
        db_uri=config['db_uri']),
        logger=logger
    )

    if rf != None:
        rf(*params)
    else:
        raise Exception('Runtime mode is not specified.')

if __name__ == '__main__':
    main()
