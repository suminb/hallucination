import os, sys
sys.path.insert(0, 'hallucination')

from hallucination import *

import logging

logger = logging.getLogger('hallucination')
logger.addHandler(logging.StreamHandler(sys.stderr))
logger.setLevel(logging.INFO)

factory = ProxyFactory(dict(
	db_uri='sqlite:///test2.db',
	logger=logger,
))

def main():
	#factory.create_db()
    #print factory.select(1)
    #factory.import_proxies(open('proxylist.txt'))
    print factory.make_request('http://static.suminb.com/test.php?sleep=2', timeout=3.75)

if __name__ == '__main__':
    main()
