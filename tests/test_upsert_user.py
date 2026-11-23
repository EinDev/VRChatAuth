import datetime
import uuid
from types import SimpleNamespace

import pytest

from conftest import USER_ID

USER_UUID = uuid.UUID(USER_ID[4:])


@pytest.fixture
def upsert_user():
    from idp.tasks import upsert_user
    return upsert_user


@pytest.fixture
def User():
    from idp.models import User
    return User


def test_creates_user_from_user_response(app, db, User, upsert_user, make_user_response):
    before = datetime.datetime.utcnow()
    vrc_user = make_user_response(
        USER_ID, "Alice",
        icon_url="",
        current_avatar_thumbnail_image_url="https://img/thumb.png")

    result = upsert_user(vrc_user)

    assert isinstance(result, User)
    stored = db.session.get(User, USER_UUID)
    assert stored is not None
    assert stored.display_name == "Alice"
    assert stored.user_icon_url == "https://img/thumb.png"
    assert stored.data_from >= before - datetime.timedelta(seconds=1)


def test_user_response_icon_url_beats_avatar_thumbnail(app, db, User, upsert_user, make_user_response):
    vrc_user = make_user_response(
        USER_ID, "Alice",
        icon_url="https://img/icon.png",
        current_avatar_thumbnail_image_url="https://img/thumb.png")

    upsert_user(vrc_user)

    assert db.session.get(User, USER_UUID).user_icon_url == "https://img/icon.png"


def test_user_icon_and_profile_pic_override_take_precedence(app, db, User, upsert_user):
    vrc_user = SimpleNamespace(
        id=USER_ID, display_name="Alice",
        user_icon="https://img/user_icon.png",
        profile_pic_override="https://img/override.png",
        icon_url="https://img/icon.png",
        current_avatar_thumbnail_image_url="https://img/thumb.png")
    upsert_user(vrc_user)
    assert db.session.get(User, USER_UUID).user_icon_url == "https://img/user_icon.png"

    vrc_user.user_icon = ""
    upsert_user(vrc_user)
    assert db.session.get(User, USER_UUID).user_icon_url == "https://img/override.png"


def test_minimal_object_without_icon_attributes_does_not_raise(app, db, User, upsert_user):
    vrc_user = SimpleNamespace(id=USER_ID, display_name="Alice")

    upsert_user(vrc_user)

    stored = db.session.get(User, USER_UUID)
    assert stored.display_name == "Alice"
    assert stored.user_icon_url is None


def test_updates_existing_user(app, db, User, upsert_user, make_user_response):
    old = datetime.datetime(2000, 1, 1)
    db.session.add(User(user_id=USER_UUID, display_name="OldName",
                        user_icon_url="https://img/old.png", data_from=old))
    db.session.commit()

    upsert_user(make_user_response(
        USER_ID, "NewName", current_avatar_thumbnail_image_url="https://img/new.png"))

    assert User.query.count() == 1
    stored = db.session.get(User, USER_UUID)
    assert stored.display_name == "NewName"
    assert stored.user_icon_url == "https://img/new.png"
    assert stored.data_from > old
