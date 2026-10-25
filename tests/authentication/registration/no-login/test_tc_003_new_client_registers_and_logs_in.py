import allure
import pytest

from config.settings import Account, get_settings
from fixtures.cleanup import Cleanup
from helpers.api.client import ApiClient, api_login
from helpers.data.unique import unique_email
from helpers.users.api import register_via_api


@pytest.mark.smoke
@pytest.mark.api
@pytest.mark.no_login
def test_tc_003_new_client_registers_and_logs_in(anonymous_api: ApiClient, cleanup: Cleanup) -> None:
    """TC-003 A new client registers through the API and can log in, an inactive user cannot."""
    email = unique_email("TC-003")
    password = "Str0ng-pass-word"

    with allure.step("register a new account"):
        user = register_via_api(anonymous_api, email, password, "Auto Tester")
        cleanup.user(user["id"])
        assert user["role"] == "client", f"a new account should be a client, got {user['role']}"
        assert user["is_active"], "a new account should be active"

    with allure.step("log in with the new account and read the profile"):
        client = api_login(Account(email, password))
        me = client.get("/auth/me").json()
        client.close()
        assert me["email"] == email, f"logged in as {me['email']} instead of {email}"

    with allure.step("registering the same email again is refused"):
        again = anonymous_api.post(
            "/auth/register",
            json={"email": email, "password": password, "full_name": "Auto Tester"},
            expected=None,
        )
        assert again.status_code == 409, f"duplicate email: expected 409, got {again.status_code}"

    with allure.step("an inactive account cannot log in"):
        response = anonymous_api.post(
            "/auth/login",
            json={"email": get_settings().inactive_email, "password": get_settings().test_password},
            expected=None,
        )
        assert response.status_code == 403, f"inactive login: expected 403, got {response.status_code}"
        assert response.json()["code"] == "ACCOUNT_INACTIVE"
