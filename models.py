from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.dialects.postgresql import UUID
from core import app

db = SQLAlchemy(app)

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
    id = db.Column(UUID, primary_key=True)
    protocol = db.Column(db.String(8))
    host = db.Column(db.String(255))
    port = db.Column(db.Integer)

    hit_ratio = db.Column(db.Float(precision=64)) # aggregated value
    access_time = db.Column(db.Float(precision=64)) # aggregated average value
    last_updated = db.Column(db.DateTime(timezone=True)) # aggregated average value

    def serialize(self):
        return serialize(self)


class AccessRecord(db.Model):
    id = db.Column(UUID, primary_key=True)
    proxy_id = db.Column(UUID)
    timestamp = db.Column(db.DateTime(timezone=True))

    user_agent = db.Column(db.String(255))
    remote_address = db.Column(db.String(64))
    
    alive = db.Column(db.Boolean)
    access_time = db.Column(db.Float(precision=64))
    status_code = db.Column(db.Integer)

    def serialize(self):
        return serialize(self)
