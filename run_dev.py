from werkzeug.serving import run_simple
from idp import create_app


class FixScriptName(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        SCRIPT_NAME = '/api'

        if environ['PATH_INFO'].startswith(SCRIPT_NAME):
            environ['PATH_INFO'] = environ['PATH_INFO'][len(SCRIPT_NAME):]
            environ['SCRIPT_NAME'] = SCRIPT_NAME
            return self.app(environ, start_response)
        else:
            start_response('404', [('Content-Type', 'text/plain')])
            return ["This doesn't get served by your FixScriptName middleware.".encode()]


run_simple('0.0.0.0', 5000, FixScriptName(create_app()), use_reloader=True)
