import datetime
import random
import string
import uuid
from typing import Union

from celery import Celery, Task, shared_task
from flask import Flask, current_app as app

from vrchatapi import LimitedUser
from .models import User, db
from idp.celery.vrc_api import VRCAPI


def upsert_user(vrc_user: LimitedUser) -> User:
    user_uuid = uuid.UUID(vrc_user.id[4:])
    user = User.query.get(user_uuid)
    if not user:
        user = User(user_id=user_uuid, display_name=vrc_user.display_name)
        db.session.add(user)
        db.session.commit()
    user.data_from = datetime.datetime.utcnow()
    if user.display_name != vrc_user.display_name:
        user.display_name = vrc_user.display_name
    if user.user_icon_url != vrc_user.user_icon:
        user.user_icon_url = vrc_user.user_icon
    db.session.add(user)
    db.session.commit()
    return user


def get_user_by_display_name(display_name: str) -> Union[User, None]:
    user_from_db: User = User.query.filter_by(display_name=display_name).first()
    if user_from_db:
        age: datetime.timedelta = datetime.datetime.utcnow() - user_from_db.data_from
        if age.seconds < 60 * 10:  # User last fetched less than 10 minutes ago, respect API rights ;-)
            return user_from_db
    try:
        user_id = load_user.delay(display_name).get()
        print(type(user_id))
        return User.query.get(user_id)
    except Exception as e:
        app.logger.warning(f"Unknown exception occurred: {e}")
        return None


@shared_task(ignore_result=False)
def load_user(user_name: str) -> Union[uuid.UUID, None]:
    vrc: VRCAPI = app.extensions["vrc"]
    vrc_user: LimitedUser = vrc.get_user(user_name)
    if not vrc_user:
        return None
    user = upsert_user(vrc_user)
    return user.user_id


@shared_task(ignore_result=True)
def check_login():
    vrc: VRCAPI = app.extensions["vrc"]
    vrc.login()


@shared_task(ignore_result=True, bind=True)
def send_code(self, user_id: uuid.UUID):
    vrc: VRCAPI = app.extensions["vrc"]
    user: User = User.query.get(user_id)
    code = ''.join([random.choice(string.digits) for _ in range(0, 4)])
    if vrc.mock_api:
        user.token = code
        db.session.add(user)
        db.session.commit()
        app.logger.info(f"Mocked Notification for user ${user}: ${code}")
        return
    vrc_uid = vrc.as_vrc_uuid(user_id)
    try:
        role_id, ann_id = vrc.send_notification(vrc_uid, f"Code: {code}",
                                                "Someone requested an authentication token for "
                                                "your account. If this was not you, ignore this message."
                                                "This token will only be valid for 10 minutes")
    except Exception as e:
        user.disabled_login = True
        db.session.add(user)
        db.session.commit()
        raise e
    user.token = code
    delete_code.apply_async((vrc_uid, role_id, ann_id), countdown=10 * 60)
    # user.delete_token_task_id = uuid.UUID(delete_task.id)
    db.session.add(user)
    db.session.commit()


@shared_task(ignore_result=True)
def delete_code(user_id: str, role_id: str, ann_id: str):
    vrc: VRCAPI = app.extensions["vrc"]
    vrc.delete_notification(user_id, role_id, ann_id)
    user_uuid = uuid.UUID(user_id[4:])
    user: User = User.query.get(user_uuid)
    user.token = None
    db.session.add(user)
    db.session.commit()


def celery_init_app(flask_app: Flask) -> Celery:
    class ContextTask(Task):
        def __call__(self, *args, **kwargs):
            with flask_app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(flask_app.name, task_cls=ContextTask, broker_connection_retry_on_startup=False)
    celery_app.config_from_object(flask_app.config['CELERY'])
    celery_app.set_default()
    flask_app.extensions["celery"] = celery_app
    return celery_app
