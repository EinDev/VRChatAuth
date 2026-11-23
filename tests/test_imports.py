import importlib

import pytest
import vrchatapi


def test_submodule_no_longer_provides_limited_user():
    """Sanity check of the premise: upstream split LimitedUser up."""
    assert not hasattr(vrchatapi, "LimitedUser")
    assert hasattr(vrchatapi, "LimitedUserSearch")
    assert hasattr(vrchatapi, "UserResponse")


@pytest.mark.parametrize("module", ["idp.celery.vrc_api", "idp.tasks", "idp"])
def test_module_imports_against_current_vrchatapi(module):
    importlib.import_module(module)
