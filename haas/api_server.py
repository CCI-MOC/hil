"""This is the HaaS API server - it provides the HaaS's rest api.

The api server is meant to be run as a stand-alone command, e.g:

    python -m haas.api_server

This is all WIP, of course.
"""

from flask import Flask, request
from haas import config, model


app = Flask(__name__)


@app.route('/')
def hello():
    return 'Hello, HaaS!'


@app.route('/user/<username>', methods=['PUT', 'DELETE'])
def user(username):
    """Handle create/modify/delete user commands.

    * A delete request will delete a user. If the user does not exists, a 404
      http status code will be returned.
    * A put request will create a user if it does not exist, and set the user's
      password otherwise.

    Right now the client doesn't get any feedback as to whether the user already
    exists or not. I don't really like the way this works right now, will have
    to sit down and come up with a proper design.
    """
    # It would be nice to have two separate functions for this. All the examples
    # in the flask docs use a simple if/else like below for this kind of thing,
    # however.
    db = model.Session()
    user = db.query(model.User).filter_by(label = username).first()

    if request.method == 'PUT':
        password = request.form['password']
        if not user:
            user = model.User(username, password)
        else:
            user.set_password(password)
        db.add(user)
    else: # DELETE
        if not user:
            return 'No such user', 404
        else:
            db.delete(user)

    db.commit()
    return ''


if __name__ == '__main__':
    config.load()
    model.init_db(create=True)
    app.run(debug=True)
