from idp import create_app
from waitress import serve
from paste.translogger import TransLogger

app = create_app()
serve(TransLogger(app, setup_console_handler=False), trusted_proxy="*",
      trusted_proxy_headers="x-forwarded-for x-forwarded-host x-forwarded-proto x-forwarded-port")
