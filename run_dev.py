from werkzeug.serving import run_simple
from idp import create_app

run_simple('0.0.0.0', 5000, create_app(), use_reloader=True)
