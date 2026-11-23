from unittest.mock import call

import pytest
import vrchatapi

from conftest import GROUP_ID, USER_ID

OTHER_ID = "usr_11111111-2222-3333-4444-555555555555"


def test_get_user_returns_full_profile_from_get_user(vrc_api, make_search_user, make_user_response):
    full = make_user_response(user_id=USER_ID, display_name="Alice",
                              current_avatar_thumbnail_image_url="https://img/thumb.png")
    vrc_api.users_a.search_users.return_value = [make_search_user(USER_ID, "Alice")]
    vrc_api.groups_a.get_group_member.return_value = object()
    vrc_api.users_a.get_user.return_value = full

    result = vrc_api.get_user("Alice")

    assert result is full
    assert isinstance(result, vrchatapi.UserResponse)
    vrc_api.users_a.search_users.assert_called_once_with(search="Alice")
    vrc_api.groups_a.get_group_member.assert_called_once_with(GROUP_ID, USER_ID)
    vrc_api.users_a.get_user.assert_called_once_with(USER_ID)


def test_get_user_raises_when_search_is_empty(vrc_api):
    vrc_api.users_a.search_users.return_value = []

    with pytest.raises(Exception):
        vrc_api.get_user("Nobody")

    vrc_api.groups_a.get_group_member.assert_not_called()
    vrc_api.users_a.get_user.assert_not_called()


@pytest.mark.parametrize("member_status", [None, False, {}])
def test_get_user_raises_when_not_group_member_and_skips_profile_fetch(
        vrc_api, make_search_user, member_status):
    vrc_api.users_a.search_users.return_value = [make_search_user(USER_ID, "Alice")]
    vrc_api.groups_a.get_group_member.return_value = member_status

    with pytest.raises(Exception):
        vrc_api.get_user("Alice")

    vrc_api.groups_a.get_group_member.assert_called_once_with(GROUP_ID, USER_ID)
    vrc_api.users_a.get_user.assert_not_called()


def test_get_user_checks_membership_before_fetching_profile(vrc_api, make_search_user, make_user_response):
    vrc_api.users_a.search_users.return_value = [make_search_user(USER_ID, "Alice")]
    order = []
    vrc_api.groups_a.get_group_member.side_effect = lambda *a, **k: order.append("member") or object()
    vrc_api.users_a.get_user.side_effect = lambda *a, **k: order.append("get_user") or make_user_response()

    vrc_api.get_user("Alice")

    assert order == ["member", "get_user"]


def test_get_user_prefers_exact_display_name_match_case_insensitive(
        vrc_api, make_search_user, make_user_response):
    vrc_api.users_a.search_users.return_value = [
        make_search_user(OTHER_ID, "Alice2"),
        make_search_user(USER_ID, "alice"),
    ]
    vrc_api.groups_a.get_group_member.return_value = object()
    vrc_api.users_a.get_user.return_value = make_user_response(USER_ID, "alice")

    vrc_api.get_user("ALICE")

    vrc_api.groups_a.get_group_member.assert_called_once_with(GROUP_ID, USER_ID)
    vrc_api.users_a.get_user.assert_called_once_with(USER_ID)


def test_get_user_falls_back_to_first_result_without_exact_match(
        vrc_api, make_search_user, make_user_response):
    vrc_api.users_a.search_users.return_value = [
        make_search_user(OTHER_ID, "Alice2"),
        make_search_user(USER_ID, "Alice3"),
    ]
    vrc_api.groups_a.get_group_member.return_value = object()
    vrc_api.users_a.get_user.return_value = make_user_response(OTHER_ID, "Alice2")

    vrc_api.get_user("Alice")

    vrc_api.groups_a.get_group_member.assert_called_once_with(GROUP_ID, OTHER_ID)
    vrc_api.users_a.get_user.assert_called_once_with(OTHER_ID)
