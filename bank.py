from sqlalchemy import MetaData
from core import app, db
from models import *

import uuid

def create_tables():
    metadata = MetaData()
    metadata.create_all(bind=db.engine)

def insert(protocol, host, port):
    """Inserts a proxy record into the database. Returns an ID of the newly created object."""

    p = Proxy(protocol=protocol, host=host, port=port)

    db.session.add(p)
    db.session.commit()

    return p.id

def update(id, **pairs):
    pass

def delete(id):
    pass

def select(n):
    """Randomly selects ``n`` proxy records."""

    if n <= 0:
        raise Exception('n must be a positive integer.')

    if n > Proxy.query.count():
        raise Exception('Not enough proxy records.')

    return Proxy.query.limit(n)

def report(id, status):
    pass


if __name__ == '__main__':
    insert('http', '202.171.253.108', 85)
    insert('http', '173.236.245.69', 80)
    insert('http', '188.142.2.102', 80)
    insert('http', '197.251.194.176', 8080)
    insert('http', '118.26.231.104', 5060)