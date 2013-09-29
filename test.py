import os, sys
sys.path.insert(0, 'hallucination')

from testify import *
from hallucination import *

import logging

logger = logging.getLogger('hallucination')
logger.addHandler(logging.StreamHandler(sys.stderr))
logger.setLevel(logging.INFO)


class DefaultTestCase(TestCase):
    @class_setup
    def init_class(self):
        self.factory = ProxyFactory(dict(
            db_uri='sqlite:///test.db',
            logger=logger,
        ))
       
    def test(self):
        #factory.make_request('http://github.com')
        pass


if __name__ == '__main__':
    run()

