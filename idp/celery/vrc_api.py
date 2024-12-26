import os
from datetime import datetime
from http.cookiejar import MozillaCookieJar
from typing import Union

from flask import Flask
from uuid import UUID

import pyotp
import vrchatapi
from vrchatapi import LimitedUser, TwoFactorAuthCode
from vrchatapi.api import authentication_api, friends_api, users_api, invite_api, groups_api
from vrchatapi.exceptions import UnauthorizedException


class VRCAPI:
    def __init__(self, username, password, group_id, mfa_code, mock_api: bool):
        self.mock_api = mock_api
        configuration = vrchatapi.Configuration(
            username=username,
            password=password
        )
        self.__api_client = vrchatapi.ApiClient(configuration)
        cookie_file = "instance/cookies.txt"
        self.__api_client.rest_client.cookie_jar = MozillaCookieJar(cookie_file)
        if os.path.isfile(cookie_file):
            self.__api_client.rest_client.cookie_jar.load()

        # Set our User-Agent as per VRChat Usage Policy
        self.__api_client.user_agent = "vrc_saml.py/1.0 vrc_saml.py@ein.dev"
        self.mfa_token = mfa_code
        self.auth_api = authentication_api.AuthenticationApi(self.__api_client)
        self.group_id = group_id
        self.friends_a = friends_api.FriendsApi(self.__api_client)
        self.users_a = users_api.UsersApi(self.__api_client)
        self.invite_a = invite_api.InviteApi(self.__api_client)
        self.groups_a = groups_api.GroupsApi(self.__api_client)

    def get_mfa_token(self) -> str:
        totp = pyotp.TOTP(self.mfa_token)
        return totp.now()

    def login(self):
        try:
            # Step 3. Calling getCurrentUser on Authentication API logs you in if the user isn't already logged in.
            current_user = self.auth_api.get_current_user()
        except UnauthorizedException as e:
            if e.status == 200:
                if "2 Factor Authentication" in e.reason:
                    self.auth_api.verify2_fa(two_factor_auth_code=TwoFactorAuthCode(self.get_mfa_token()))
                else:
                    raise Exception("Unknown error: " + e.reason)
                current_user = self.auth_api.get_current_user()
            else:
                raise e
        except vrchatapi.ApiException as e:
            raise e
        self.__api_client.rest_client.cookie_jar.save()
        print("Logged in as:", current_user.display_name)

    def get_user(self, user_name: str) -> LimitedUser:
        user_result = self.users_a.search_users(search=user_name)
        if len(user_result) == 0:
            raise Exception("User not found.")

        user_id = user_result[0].id

        member_status = self.groups_a.get_group_member(self.group_id, user_id)
        if not member_status:
            raise Exception("User is not a member of the group.")

        return user_result[0]

    def send_notification(self, user_id, title, text) -> (str, Union[str, None]):
        role = None
        assignment = None
        ann = None
        try:
            role = self.groups_a.create_group_role(self.group_id, create_group_role_request={
                "name": f"Notif_{datetime.now().strftime('%Y%m%d%H%M')}",
                "isSelfAssignable": False
            })
            assignment = self.groups_a.add_group_member_role(self.group_id, user_id, role.id)
            ann = self.groups_a.create_group_announcement(self.group_id, create_group_announcement_request={
                "roleIds": [role.id],
                "sendNotification": True,
                "text": text,
                "title": title,
                "visibility": "group"
            })
            return role.id, ann.id
        except Exception as e:
            # Reverse already partially sent API requests before re-throwing
            if ann:
                self.groups_a.delete_group_announcement(self.group_id, ann.id)
            if assignment:
                self.groups_a.remove_group_member_role(self.group_id, user_id, role.id)
            if role:
                self.groups_a.delete_group_role(self.group_id, role.id)
            raise e

    def delete_notification(self, user_id, role_id, ann_id):
        self.groups_a.remove_group_member_role(self.group_id, user_id, role_id)
        self.groups_a.delete_group_role(self.group_id, role_id)
        self.groups_a.delete_group_announcement(self.group_id, ann_id)

    @staticmethod
    def as_vrc_uuid(data: UUID) -> str:
        return "usr_" + str(data)


def vrc_init_app(app: Flask) -> VRCAPI:
    cfg = app.config["VRC"]
    vrc_api = VRCAPI(cfg.get('USERNAME'),
                     cfg.get('PASSWORD'),
                     cfg.get('GROUP_ID'),
                     cfg.get('MFA_CODE'),
                     str(cfg.get('MOCK_API')).lower() != "false")
    app.extensions["vrc"] = vrc_api
    return vrc_api
