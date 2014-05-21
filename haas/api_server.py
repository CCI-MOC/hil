"""This is the HaaS API server - it provides the HaaS's rest api.

The api server is meant to be run as a stand-alone command, e.g:

    python -m haas.api_server

This is all WIP, of course.
"""

from flask import Flask
from haas import config, model


app = Flask(__name__)


@app.route('/')
def hello():
    return 'Hello, HaaS!'

if __name__ == '__main__':
    config.load()
    model.init_db(create=True)
    app.run(debug=True)
