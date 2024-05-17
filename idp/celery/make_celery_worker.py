from idp import create_vrc_worker

flask_app = create_vrc_worker()
celery_app = flask_app.extensions["celery"]
