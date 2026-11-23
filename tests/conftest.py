"""Shared fixtures for the IdP test-suite.

Production modules (``idp.*``) are imported lazily inside fixtures so that an
import error in one module shows up as a failure of the tests that need it,
instead of aborting collection of the whole suite.
"""
from unittest.mock import MagicMock

import pytest
import vrchatapi
from flask import Flask


USER_ID = "usr_c1644b5b-3ca4-45b4-97c6-a2a0de70d469"
GROUP_ID = "grp_00000000-0000-0000-0000-000000000000"


@pytest.fixture
def vrc_config():
    """A vrchatapi Configuration with client-side validation disabled, so model
    objects can be built with only the fields a test cares about."""
    cfg = vrchatapi.Configuration()
    cfg.client_side_validation = False
    return cfg


@pytest.fixture
def make_search_user(vrc_config):
    def _make(user_id=USER_ID, display_name="Some User", **kwargs):
        return vrchatapi.LimitedUserSearch(
            id=user_id, display_name=display_name,
            local_vars_configuration=vrc_config, **kwargs)
    return _make


@pytest.fixture
def make_user_response(vrc_config):
    def _make(user_id=USER_ID, display_name="Some User", **kwargs):
        return vrchatapi.UserResponse(
            id=user_id, display_name=display_name,
            local_vars_configuration=vrc_config, **kwargs)
    return _make


@pytest.fixture
def vrc_api(tmp_path, monkeypatch):
    """A VRCAPI instance whose users/groups API objects are MagicMocks.

    VRCAPI.__init__ points a MozillaCookieJar at the relative path
    ``instance/cookies.txt``, so run inside an empty temp dir."""
    monkeypatch.chdir(tmp_path)
    from idp.celery.vrc_api import VRCAPI

    api = VRCAPI("user", "pass", GROUP_ID, "JBSWY3DPEHPK3PXP", mock_api=True)
    api.users_a = MagicMock(name="users_a")
    api.groups_a = MagicMock(name="groups_a")
    return api


@pytest.fixture
def app():
    """Minimal Flask app bound to the IdP's SQLAlchemy instance, using an
    in-memory sqlite database (avoids create_app's redis/celery config)."""
    from idp.models import db

    flask_app = Flask("idp-tests")
    flask_app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    db.init_app(flask_app)
    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def db(app):
    from idp.models import db as _db
    return _db
