import re

import allure
import pytest

from fixtures.cleanup import Cleanup
from helpers.api.client import ApiClient
from helpers.cars.api import create_car_via_api

MONEY = re.compile(r"(€|\$|£|\beur\b|\beuro|\busd\b|\bprice\b|\bper day\b|\d+[.,]\d{2})", re.IGNORECASE)


@pytest.mark.regression
@pytest.mark.api
@pytest.mark.llm
@pytest.mark.costly
@pytest.mark.client
def test_tc_011_generated_description_follows_the_rules(
    client_api: ApiClient, second_client_api: ApiClient, cleanup: Cleanup
) -> None:
    """TC-011 The generated description names make, model and year, is at most 600 characters and has no price."""
    with allure.step("a client lists a Skoda Octavia from 2021 at 42.50 per day"):
        car = create_car_via_api(
            client_api, "TC-011", make="Skoda", model="Octavia", year=2021, daily_price=42.50,
            features=["gps", "rear_camera"],
        )  # fmt: skip
        cleanup.car(car["id"])

    with allure.step("ask for a generated description"):
        result = client_api.post(f"/cars/{car['id']}/generate-description").json()
        text = result["description"]
        allure.attach(text, name=f"description from {result['provider']}")

    with allure.step("the description follows every rule"):
        problems = []
        if not 0 < len(text) <= 600:
            problems.append(f"length is {len(text)}, must be 1 to 600")
        for word in ("Skoda", "Octavia", "2021"):
            if word.lower() not in text.lower():
                problems.append(f"does not mention {word}")
        if match := MONEY.search(text):
            problems.append(f"mentions money ({match.group(0)!r})")
        if "**" in text or text.lstrip().startswith("#"):
            problems.append("contains markdown")
        assert not problems, (
            f"description from {result['provider']} breaks the rules: {problems}. Text: {text!r}"
        )

    with allure.step("another client cannot ask for a description of this car"):
        other = second_client_api.post(f"/cars/{car['id']}/generate-description", expected=None)
        assert other.status_code == 403, f"another client: expected 403, got {other.status_code}"
