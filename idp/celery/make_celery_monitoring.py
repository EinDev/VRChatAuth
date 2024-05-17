from idp import create_monitoring_worker

flask_app = create_monitoring_worker()
celery_app = flask_app.extensions["celery"]
