from __init__ import ProxyFactory
from models import Proxy

import getopt
import os, sys
import logging

logger = logging.getLogger('hallucination')
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.INFO)


def testrun(proxy_factory):
    url = 'http://translator.suminb.com'
    for row in proxy_factory.session.query(Proxy).all():
        try:
            logger.info('Test run: Fetching %s via %s' % (url, row))
            r = proxy_factory.make_request(url, proxy=row)
        except Exception as e:
            logger.error(str(e))


def _import():
    """Imports a list of proxy servers from a text file."""
    pass


def export():
    """Exports the list of proxy servers to the standard output."""
    pass


def main():
    opts, args = getopt.getopt(sys.argv[1:], 'tix')

    rf = None
    for o, a in opts:
        if o == '-t':
            rf = testrun
        elif o == '-i':
            rf = _import
        elif o == '-x':
            rf = export

    if rf != None:
        factory = ProxyFactory(config=dict(db_uri='sqlite:///test.db'))
        rf(factory)
    else:
        raise Exception('Runtime mode is not specified.')

if __name__ == '__main__':
    main()
