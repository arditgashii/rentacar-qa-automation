import allure
import pytest
from playwright.sync_api import Page, expect

from helpers.api.client import ApiClient
from helpers.auth.login import login_as
from helpers.data.wait import wait_until
from pages.admin.admin_dashboard_page import AdminDashboardPage
from pages.components.navbar import Navbar


@pytest.mark.smoke
@pytest.mark.ui
@pytest.mark.admin
def test_tc_001_admin_logs_in_and_sees_the_dashboard(page: Page, admin_api: ApiClient) -> None:
    """TC-001 Admin logs in and sees the dashboard stats."""
    dashboard = AdminDashboardPage(page)

    with allure.step("log in as an admin"):
        login_as(page, "admin")

    with allure.step("the admin lands on the dashboard with the admin menu"):
        expect(page, "an admin should land on /admin after login").to_have_url("/admin")
        expect(Navbar(page).admin_dashboard, "the admin menu is missing").to_be_visible()
        expect(dashboard.stats, "the stat tiles are missing").to_be_visible()

    with allure.step("the tiles show the same numbers as the API"):
        # Other workers add and remove cars in parallel, so the page and the API are read together
        # and the page is reloaded until both describe the same moment.
        last: dict[str, tuple[str, str]] = {}

        def tiles_match_api() -> bool:
            stats = admin_api.get("/admin/stats").json()
            page.reload()
            for tile, key in ((dashboard.cars, "cars"), (dashboard.users, "users"),
                              (dashboard.active_bookings, "active_bookings")):  # fmt: skip
                last[key] = (tile.inner_text(), str(stats[key]))
            return all(shown == expected for shown, expected in last.values())

        wait_until(
            tiles_match_api,
            timeout=20,
            message=lambda: (
                "dashboard tiles differ from the API: "
                + ", ".join(f"{key} shows {shown}, API says {api}" for key, (shown, api) in last.items())
            ),
        )
