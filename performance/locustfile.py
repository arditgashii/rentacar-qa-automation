"""Load test for DriveNow.

Two kinds of users: browsers (most of the traffic: list, filter, open a car) and bookers (log in, book,
cancel, so the data stays clean). Thresholds are checked when the run ends; the process exits with 1
when p95 latency or the error rate is too high, so CI can fail on it.

    locust -f performance/locustfile.py --headless -u 20 -r 5 -t 1m --host http://localhost:8000
"""

import random
from datetime import date, timedelta
from itertools import count

from locust import HttpUser, between, events, task
from locust.env import Environment

P95_LIMIT_MS = 500
ERROR_RATE_LIMIT = 0.01
CITIES = ["Prishtina", "Prizren", "Peja", "Gjakova", "Ferizaj", "Tirana"]
CATEGORIES = ["economy", "compact", "suv", "van", "luxury", "electric"]
CLIENTS = [f"client{n}@drivenow.test" for n in range(1, 7)]
PASSWORD = "DriveNow!2026"
_dates = count()


class Browser(HttpUser):
    weight = 4
    wait_time = between(0.5, 2)

    def on_start(self) -> None:
        self.car_ids: list[int] = []

    @task(3)
    def list_cars(self) -> None:
        response = self.client.get("/api/v1/cars", params={"page_size": 12}, name="/api/v1/cars")
        if response.ok:
            self.car_ids = [car["id"] for car in response.json()["items"]]

    @task(2)
    def filter_cars(self) -> None:
        params = {"city": random.choice(CITIES), "category": random.choice(CATEGORIES), "max_price": 80}
        self.client.get("/api/v1/cars", params=params, name="/api/v1/cars?filters")

    @task(2)
    def open_car(self) -> None:
        if self.car_ids:
            self.client.get(f"/api/v1/cars/{random.choice(self.car_ids)}", name="/api/v1/cars/{id}")

    @task(1)
    def browse_page(self) -> None:
        self.client.get("/cars", name="/cars (page)")


class Booker(HttpUser):
    weight = 1
    wait_time = between(1, 3)

    def on_start(self) -> None:
        response = self.client.post(
            "/api/v1/auth/login", json={"email": random.choice(CLIENTS), "password": PASSWORD}
        )
        self.headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
        self.me = self.client.get("/api/v1/auth/me", headers=self.headers).json()["id"]

    @task
    def book_and_cancel(self) -> None:
        cars = self.client.get("/api/v1/cars", params={"page_size": 50}, name="/api/v1/cars").json()["items"]
        others = [car for car in cars if car["owner_id"] != self.me]
        if not others:
            return
        # Far in the future and spread out, so parallel bookers rarely ask for the same dates.
        start = date.today() + timedelta(days=200 + next(_dates) % 300)
        payload = {
            "car_id": random.choice(others)["id"],
            "start_date": start.isoformat(),
            "end_date": (start + timedelta(days=2)).isoformat(),
        }
        with self.client.post(
            "/api/v1/bookings",
            json=payload,
            headers=self.headers,
            name="/api/v1/bookings",
            catch_response=True,
        ) as response:
            if response.status_code == 409:
                response.success()  # dates already taken by another simulated user: expected, not an error
                return
        if response.status_code == 201:
            self.client.post(
                f"/api/v1/bookings/{response.json()['id']}/cancel",
                headers=self.headers,
                name="/api/v1/bookings/{id}/cancel",
            )


@events.quitting.add_listener
def check_thresholds(environment: Environment, **_: object) -> None:
    stats = environment.stats.total
    p95 = stats.get_response_time_percentile(0.95) or 0
    print(f"Thresholds: p95 {p95:.0f} ms (limit {P95_LIMIT_MS}), ", end="")
    print(f"errors {stats.fail_ratio:.2%} (limit {ERROR_RATE_LIMIT:.0%})")
    if p95 > P95_LIMIT_MS or stats.fail_ratio > ERROR_RATE_LIMIT:
        environment.process_exit_code = 1
