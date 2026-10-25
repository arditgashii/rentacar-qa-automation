# DriveNow QA automation

A Python test automation framework for [DriveNow](https://github.com/arditgashii/rentacar-platform),
a rent-a-car marketplace. It tests the product the way a user and an integrator see it: through the
browser (Playwright), through the REST API (httpx), inside its Azure dependencies (Blob Storage and
Service Bus), and under load (Locust).

DriveNow ships with four intentional bugs. The suite catches all four with readable failures, and
passes completely when the bugs are switched off:

```
FAILED TC-005  saved car differs from what the admin entered: daily_price: expected 89.99, got 89.0
FAILED TC-006  search results: expected ['SUV at exactly the max price', 'cheaper SUV'], got ['cheaper SUV']
FAILED TC-008  an overlapping booking was accepted: expected 409 DATES_TAKEN, got 201
FAILED TC-009  another client could delete the car: expected 403, got 204 and the car was deleted
4 failed, 8 passed in 20s   (pytest -n 3)
```

## What is in it

| | |
|---|---|
| **Tests** | 12 test cases: login, logout, registration, listing with photo upload, update, search, booking, double booking, authorization, delete, LLM output. [docs/TEST-CASES.md](docs/TEST-CASES.md) |
| **Structure** | `tests/<section>/<module>/<feature>/<role>/test_tc_xxx_<slug>.py`, one file per test case, page objects, helpers, fixtures. [docs/TEST-STRUCTURE.md](docs/TEST-STRUCTURE.md) |
| **UI** | Playwright for Python through `pytest-playwright`, `data-testid` locators, trace, screenshot and video kept on failure |
| **API** | httpx client that turns an unexpected status into a readable failure |
| **Azure** | Checks that uploaded photos exist in Blob Storage and that booking events reach the Service Bus topic |
| **LLM** | TC-011 checks the guardrails of the generated description (length, facts, no prices, no markdown) |
| **Parallel** | `pytest-xdist`; each worker leases its own accounts from a pool |
| **Isolation** | Unique data per test, `cleanup` fixture removes everything through the API, even when the test fails |
| **Reports** | JUnit XML, self-contained HTML, Allure results with steps and attachments |
| **Performance** | Locust with browsing and booking users and p95/error-rate thresholds |
| **CI** | GitHub Actions and Azure DevOps YAML: lint, mypy, e2e with the bugs on and off, optional load test |

## Run it

1. Start DriveNow (in the platform repo): `docker compose up -d --build --wait`
2. Install:

   ```bash
   py -3.12 -m venv .venv && .venv/Scripts/activate      # source .venv/bin/activate on Linux/macOS
   pip install -r requirements.txt
   playwright install chromium
   cp .env.example .env
   ```

3. Run:

   ```bash
   pytest -n 3                                   # everything, 3 workers
   pytest -m smoke                               # the short critical set
   pytest tests/fleet                            # one area
   pytest -m "not costly"                        # never call a paid LLM
   pytest --headed --slowmo 300 -k tc_004        # watch one test in the browser
   pytest -n 3 --junitxml=reports/junit.xml --html=reports/report.html --self-contained-html --alluredir=reports/allure-results
   python scripts/check_results.py reports/junit.xml   # exactly the four known bugs failed?
   locust -f performance/locustfile.py --headless -u 20 -r 5 -t 1m --host http://localhost:8000
   ```

   `allure serve reports/allure-results` opens the Allure report (needs the Allure CLI).
   `KEEP_DATA=1 pytest ...` keeps the data a test created, for debugging.

## Configuration

All settings have defaults for the local Docker stack; `.env.example` lists them.

| Variable | Meaning |
|---|---|
| `BASE_URL` | Where DriveNow runs |
| `TEST_PASSWORD`, `POOL_ADMIN`, `POOL_CLIENT`, `INACTIVE_EMAIL` | Seeded accounts; each worker leases 1 admin and 2 clients |
| `AZURE_STORAGE_CONNECTION_STRING`, `SERVICEBUS_CONNECTION_STRING` | Optional; enable the checks inside Azure |
| `KEEP_DATA` | `1` skips cleanup |
| `TIMEOUT_MS` | Default Playwright timeout |

## Layout

```
config/          settings, account pools and leasing
data/            test data and upload files
fixtures/        logged-in API clients, cleanup
helpers/         api/ auth/ cars/ bookings/ users/ azure/ data/
pages/           page objects and components
tests/           authentication/ fleet/ bookings/  (section/module/feature/role)
performance/     Locust load test
scripts/         check_results.py
docs/            TEST-STRUCTURE.md, TEST-CASES.md, DECISIONS.md
```

## CI

`.github/workflows/tests.yml` checks out this repo and the platform, starts the platform with Docker
Compose, and runs the suite twice: with `DRIVENOW_BUGS=on` (the build passes only if exactly the four
listed tests fail, see `expected-failures.txt`) and with `DRIVENOW_BUGS=off` (everything must pass).
Reports are uploaded as artifacts. The same pipeline exists for Azure DevOps in `azure-pipelines.yml`,
with `PublishTestResults` for the JUnit report and a manual Locust stage.

## Where each skill is shown

| Skill | Where |
|---|---|
| Python, pytest, fixtures, markers, xdist | everything; `conftest.py`, `fixtures/`, `pyproject.toml` |
| REST API testing | `helpers/api/client.py`, TC-003, TC-006 to TC-009, TC-011 |
| UI automation (Playwright) | `pages/`, TC-001, TC-002, TC-004, TC-005, TC-010, TC-012 |
| Azure Blob Storage and Service Bus | `helpers/azure/`, TC-004, TC-007 |
| Security and authorization testing | TC-002, TC-003, TC-009, TC-011, TC-012 |
| Testing an LLM feature | TC-011 |
| Regression and smoke sets | markers `smoke`, `regression` |
| Performance testing (Locust) | `performance/locustfile.py` |
| CI/CD (GitHub Actions, Azure DevOps YAML) | `.github/workflows/tests.yml`, `azure-pipelines.yml` |
| Docker | CI starts the platform with Docker Compose |
| Reporting | JUnit, HTML, Allure, `scripts/check_results.py` |
