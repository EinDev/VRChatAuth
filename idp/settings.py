import os.path

OAUTH2_REFRESH_TOKEN_GENERATOR = True
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_DATABASE_URI = 'sqlite:///db.sqlite'
VRC = {
    'COOKIE_FILE': os.path.abspath(os.path.join("instance", "cookies.txt"))
}
CELERY = {
    'broker_url': "redis://redis",
    'result_backend': "redis://redis"
}
RATELIMIT_STORAGE_URI = "redis://redis"
