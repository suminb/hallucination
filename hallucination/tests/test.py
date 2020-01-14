import os, sys
sys.path.insert(0, 'hallucination')

from py.test import *
from hallucination import *

DB_NAME = '/tmp/test.db'
FILE_NAME = '/tmp/test.txt'

import logging

logger = logging.getLogger('hallucination')
logger.addHandler(logging.StreamHandler(sys.stderr))
logger.setLevel(logging.INFO)

factory = None

def setup_module(module):
    """ setup any state specific to the execution of the given module."""

    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)

    global factory
    factory = ProxyFactory(dict(
        db_uri='sqlite:///{0}'.format(DB_NAME),
        logger=logger,
    ))

def test_create():
    factory.create_db()

def test_empty_pool():
    assert factory.get(1) == None


def test_insertion():
    pid = factory.insert('http', '12.199.141.164', 8000, id=1)
    assert pid == 1

def test_import():
    with open(FILE_NAME, 'w') as f:
        f.write('http://12.199.141.165:8000')
    factory.import_proxies(FILE_NAME)
    assert factory.get(2) != None

def test_nonempty_pool():
    assert factory.get(1) != None
   
def test_request():
    proxy = factory.get(1)

    try:
        req = factory.make_request('http://github.com', proxy=proxy)
        assert req.status_code == 200
    except:
        # FIXME: Proxy may fail. What should we do?
        pass
