import os, sys
sys.path.insert(0, 'hallucination')

from testify import *
from hallucination import *

import logging

logger = logging.getLogger('hallucination')
logger.addHandler(logging.StreamHandler(sys.stderr))
logger.setLevel(logging.INFO)


class DefaultTestCase(TestCase):
    DB_NAME = 'test.db'

    @class_setup
    def init_class(self):

        if os.path.exists(self.DB_NAME):
            os.remove(self.DB_NAME)

        self.factory = ProxyFactory(dict(
            db_uri='sqlite:///{}'.format(self.DB_NAME),
            logger=logger,
        ))

    def test_create(self):
        self.factory.create_db()

    def test_empty_pool(self):
        assert_equal(self.factory.get(1), None)

    def test_insertion(self):
        pid = self.factory.insert('http', 'localhost', 8080)
        assert_equal(pid, 1)

    def test_nonempty_pool(self):
        assert_not_equal(self.factory.get(1), None)
       
    def test(self):
        #factory.make_request('http://github.com')
        pass


    @class_teardown
    def clear_class(self):
        pass


if __name__ == '__main__':
    run()

