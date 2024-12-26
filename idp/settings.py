import os.path

from celery.schedules import crontab

OAUTH2_REFRESH_TOKEN_GENERATOR = True
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_DATABASE_URI = 'sqlite:///db.sqlite'
VRC = {
    'COOKIE_FILE': os.path.abspath(os.path.join("instance", "cookies.txt")),
    'MOCK_API': True
}
CELERY = {
    'broker_url': "redis://redis",
    'result_backend': "redis://redis",
    'beat_schedule': {
        'check-login': {
            'task': 'idp.tasks.check_login',
            'schedule': crontab(minute=20)
        }
    }
}
RATELIMIT_STORAGE_URI = "redis://redis"
