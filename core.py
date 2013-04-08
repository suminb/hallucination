from flask import Flask, jsonify, request

import os, sys
import uuid
import datetime

import config

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = config.DB_URI

from models import *


def get_remote_address(req):
    if not req.headers.getlist('X-Forwarded-For'):
        return req.remote_addr
    else:
        return req.headers.getlist('X-Forwarded-For')[0]


@app.route('/')
def index():

    p = Proxy(id=str(uuid.uuid4()), protocol='http', host='54.235.210.159', port=80)

    db.session.add(p)
    db.session.commit()

    return ''


@app.route('/v0.8/add', methods=['POST'])
def add():
    protocol = request.form.get('protocol')
    host = request.form.get('host')
    port = request.form.get('port')

    try:
        proxy = Proxy(id=str(uuid.uuid4()), protocol=protocol, host=host, port=port)

        db.session.add(proxy)
        db.session.commit()

    except Exception as e:
        return str(e) + '\n', 500

    return ''


@app.route('/v0.8/get')
def get():
    """Returns a single IP address of a proxy server.
    """

    from random import randint

    rows = Proxy.query.order_by(Proxy.access_time.desc()).limit(10).all()
    n = len(rows)

    return jsonify(rows[randint(0, n-1)].serialize())


@app.route('/v0.8/report', methods=['POST'])
def report():
    """Receives status information regarding a proxy server
    """
    protocol = request.form.get('protocol')
    host = request.form.get('host')
    port = request.form.get('port')

    try:
        proxy = Proxy.query.filter_by(protocol=protocol, host=host, port=port).first()

        record = AccessRecord(id=str(uuid.uuid4()))
        record.proxy_id = proxy.id
        record.timestamp = datetime.datetime.now()

        record.user_agent = request.headers.get('User-Agent')
        record.remote_address = get_remote_address(request)

        for key in ('alive', 'access_time', 'status_code'):
            setattr(record, key, request.form[key])

        record.timestamp = datetime.datetime.now()
        print record.serialize()

        db.session.add(record)
        db.session.commit()

    except Exception as e:
        return str(e) + '\n', 500

    return ''

if __name__ == '__main__':
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    debug = bool(os.environ.get('DEBUG', 0))

    app.run(host=host, port=port, debug=debug)


if app.config['DEBUG']:
    from werkzeug import SharedDataMiddleware
    import os
    app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
      '/': os.path.join(os.path.dirname(__file__), 'static')
    })
