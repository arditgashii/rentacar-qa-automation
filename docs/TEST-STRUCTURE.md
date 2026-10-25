# Test structure (the rulebook)

Every test in this repo follows these rules. If a test does not fit, the rule is changed here first,
in the same change, never bypassed.

## 1. The path rule

```
tests/<ui-section>/<module>/<feature>/<role>/test_tc_xxx_<slug>.py
```

- The folders follow the product: section, then module, then feature.
- **The role is always the last folder.** Role folders: `admin`, `client`, `no-login` (flows that
  happen before anyone logs in, or that anyone can do without an account).
- A role folder exists only when that role reaches the feature in the product. A test that proves a
  role is **refused** lives with the role that tries (TC-009 is a client trying to delete a car).

The tree (roles in brackets are the only role folders that exist):

```
tests/
  authentication/
    login/                  [admin]
    invalid-login/          [no-login]
    registration/           [no-login]
  fleet/
    cars/
      create/               [client]
      update/               [admin]
      search/               [no-login]
      delete/               [client, admin]
      generate-description/ [client]
  bookings/
    booking/
      create/               [client]
```

## 2. One file = one test case

- File name: `test_tc_<number>_<slug>.py`, slug in snake_case. Example:
  `test_tc_004_client_creates_a_listing_with_photos.py`.
- **Exactly one test function per file**, named like the file.
- The docstring starts with the ID and the title from [TEST-CASES.md](TEST-CASES.md):
  `"""TC-004 Client creates a listing with 3 photos; ..."""`.
- The body is split into `with allure.step("...")` blocks that read like the steps of the test case.
- Every assertion has a message a person understands without reading the code, for example
  `daily_price: expected 89.99, got 89.0`.

## 3. IDs

`TC-001`, `TC-002`, ... Never reused. The ID links a file to its row in [TEST-CASES.md](TEST-CASES.md)
and, in the QA Hub dashboard, to the test case in Test Plans.

## 4. Markers (instead of tags)

Registered in `pyproject.toml`; `--strict-markers` refuses anything else.

| Marker | Meaning |
|---|---|
| `smoke` | short, critical check, runs first |
| `regression` | the full behaviour of a feature |
| `api`, `ui` | how the test talks to the product |
| `integration` | also looks inside an Azure dependency (Blob Storage, Service Bus) |
| `security` | checks an authorization or access rule |
| `llm` | checks the output of the LLM feature |
| `costly` | spends money when a real provider is configured (TC-011 with `LLM_PROVIDER=anthropic`) |
| `admin`, `client`, `no_login` | the role the test acts as |
| `known_bug("BUG-00x")` | fails because of a known product bug; metadata only, the test still fails |

Areas and teams live in markers and folders, never in file names.

```bash
pytest -m smoke                 # the short critical set
pytest -m "api and not costly"  # API tests that never spend money
```

## 5. Isolation

- Every test creates the data it needs with unique names (`AUTO TC-004 Car 4812934120`) and
  registers it with the `cleanup` fixture right after creating it. Cleanup runs after the test, passed
  or failed, newest first, through the API with an admin account. A failed cleanup fails the test.
  `KEEP_DATA=1` keeps the data.
- Users cannot be deleted in DriveNow, so cleanup deactivates the accounts a test registered.
- A test never depends on another test or on the order tests run in.
- **Never hard-code an account.** A test asks for a role (`login_as(page, "admin")`,
  `client_api`, `second_client_api`) and `config/settings.py` leases the account from its pool:
  each xdist worker gets one admin and two clients of its own. With 6 seeded clients the suite runs
  with at most `-n 3`.

## 6. Black-box

Never import code from `rentacar-platform`. Find elements by `data-testid` (the full list is in the
platform's `docs/TESTIDS.md`) and set up or clean data through the public REST API.

## 7. Where the other code goes

| Folder | What |
|---|---|
| `pages/` | page objects: one class per page, locators and actions, no business assertions |
| `pages/components/` | parts used on many pages: `Flash`, `ConfirmDialog`, `Navbar` |
| `helpers/` | actions reused by many tests, grouped by area: `api/`, `auth/`, `cars/`, `bookings/`, `users/`, `azure/`, `data/` |
| `fixtures/` | pytest fixtures: logged-in API clients, `cleanup` |
| `data/` | static test data and upload files |
| `config/` | settings, account pools and leasing |
| `performance/` | Locust load test |
| `scripts/` | tools that are not tests (`check_results.py`) |

## 8. Reusable building blocks

Never re-implement a login, a confirmation or a flash check inside a test. Use these:

| Building block | Use it for |
|---|---|
| `helpers.auth.login.login_as(page, role)` | logs the browser in with the worker's account |
| `helpers.api.client.api_login(account)`, fixtures `admin_api`, `client_api`, `second_client_api`, `anonymous_api` | REST calls; `expected=` turns a wrong status into a readable failure |
| `helpers.cars.api` | `create_car_via_api`, `get_car_via_api`, `search_cars_via_api`, `car_exists` |
| `helpers.bookings.api` | `book_car_via_api` (returns the raw response, so refusals can be checked), `notifications_for_booking` |
| `helpers.azure.blob`, `helpers.azure.servicebus` | look inside Azurite and peek the Service Bus `audit` subscription |
| `helpers.data.unique` | `unique_name`, `unique_plate`, `unique_email`, `unique_city` |
| `helpers.data.wait.wait_until` | wait for an eventually true condition (no `sleep` in tests) |
| `pages.cars.car_form_page.CarFormPage` | create and edit form: `fill({...})`, `attach_photos`, `save`, `photo_items` |
| `pages.admin.admin_cars_page.AdminCarsPage` | `search`, `row`, `edit`, `delete` (with the confirmation) |
| `pages.components.flash.Flash` | `expect_success(text)`, `expect_error(text)` |

## 9. Adding a test

1. Write the test case in [TEST-CASES.md](TEST-CASES.md) with the next free ID.
2. Create the folders with the path rule, only the role folders that reach the feature, and add the
   branch to the tree in section 1 in the same change.
3. One file, one function, steps, readable assertions, cleanup.
4. If it fails on purpose because of a product bug, add `known_bug` and a line in `expected-failures.txt`.
