"""Module declaring the flask app

This exposes exactly one symbol, `app`, which is our flask app. Declaring
this in the same module as other things quickly leads to headaches trying
to avoid circular dependencies.

In particular, it's common to have structures like:

    * Module A needs to access the app
    * Module B Also needs to access the app
    * Module A requires module B

If the app is defined in module A, this results in a dependency cycle.
The easiest way to avoid this is to have the app defined in a module that
does (almost) nothing else, and thus has few dependencies.
"""
import flask

app = flask.Flask(__name__.split('.')[0])
