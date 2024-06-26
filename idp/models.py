import time
import datetime

from flask_sqlalchemy import SQLAlchemy
from authlib.integrations.sqla_oauth2 import (
    OAuth2ClientMixin,
    OAuth2AuthorizationCodeMixin,
    OAuth2TokenMixin,
)
from sqlalchemy import ForeignKey

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'user'
    user_id = db.Column(db.UUID, primary_key=True)
    token = db.Column(db.String(4))
    # delete_token_task_id = db.Column(db.UUID)
    display_name = db.Column(db.String(30))
    user_icon_url = db.Column(db.String(100))
    disabled_login = db.Column(db.Boolean, default=False)
    data_from = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)

    def get_user_id(self):
        return self.user_id

    def is_code_valid(self, code: str):
        return code is not None and len(code) == 4 and self.token == code


class OAuth2Client(db.Model, OAuth2ClientMixin):
    __tablename__ = 'oauth2_client'

    id = db.Column(db.Integer, primary_key=True)


class OAuth2AuthorizationCode(db.Model, OAuth2AuthorizationCodeMixin):
    __tablename__ = 'oauth2_code'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.UUID, db.ForeignKey('user.user_id', ondelete='CASCADE'))
    user = db.relationship('User')


class OAuth2Token(db.Model, OAuth2TokenMixin):
    __tablename__ = 'oauth2_token'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.UUID, db.ForeignKey('user.user_id', ondelete='CASCADE'))
    user = db.relationship('User')

    def is_refresh_token_active(self):
        if self.revoked:
            return False
        expires_at = self.issued_at + self.expires_in * 2
        return expires_at >= time.time()
