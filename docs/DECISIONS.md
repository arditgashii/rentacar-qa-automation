# Decisions

- **The structure mirrors a real project.** The layout (`pages/`, `helpers/`, `fixtures/`, `data/`,
  `config/`, `tests/<section>/<module>/<feature>/<role>/`) is the one I use at work for a
  TypeScript Playwright suite, translated into idiomatic Python and pytest.
- **`--import-mode=importlib`** lets the test folders follow the product menu with hyphens
  (`invalid-login`, `no-login`) and without `__init__.py` files.
- **Steps are `allure.step` blocks** so the Allure report reads like the test case, and assertion
  messages say what was expected and what came back.
- **No `xfail` for the known bugs.** The four tests fail for real; `expected-failures.txt` and
  `scripts/check_results.py` keep CI green only while exactly those four fail. If a bug is fixed or a
  new failure appears, CI goes red.
- **CI runs the suite twice**: with the bugs on (four expected failures) and off (everything passes).
- **The full suite runs in CI, including TC-011**, because the platform uses the free mock LLM there.
  `costly` only matters with a real provider; `-m "not costly"` leaves it out.
- **Parallel runs with leased accounts.** Each xdist worker leases one admin and two clients, so no
  two workers share an account. JWT sessions are stateless, so a browser and an API client can use
  the same account at the same time.
- **Dashboard numbers are compared at the same moment.** Other workers create and delete cars, so
  TC-001 reloads the page until the page and the API agree instead of comparing two different moments.
- **Service Bus is peeked, not received.** The test reads the `audit` subscription with `peek`, so it
  never takes a message away from the platform's worker.
- **Azure checks are optional.** Without connection strings the integration tests still check the
  product through the API and skip only the look inside Azure, so the suite also runs against a
  deployment where the storage is not reachable.
- **Only page objects that a test uses exist.** No speculative page classes.
