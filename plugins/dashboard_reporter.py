"""Results for the QA Hub dashboard.

--dashboard-catalog=<file>   with --collect-only: every collected test as JSON (path, ID, title, markers)
--dashboard-dir=<folder>     progress.jsonl (one JSON line per event, read live by the dashboard) and
                             report.json (the full result) when the run ends

Works with and without xdist: the process that runs a test attaches its details to the report, and the
main process (the only one that sees every report) writes the files.
"""

import json
import re
import time
from pathlib import Path
from typing import Any

import allure_commons
import pytest

TC_ID = re.compile(r"^TC-\d{3,}")
KNOWN_MARKERS = {
    "smoke", "regression", "api", "ui", "integration", "security", "llm", "costly",
    "admin", "client", "no_login", "known_bug",
}  # fmt: skip
CODE_ERRORS = (TypeError, AttributeError, NameError, KeyError, IndexError, ImportError)
ENVIRONMENT = re.compile(
    r"ConnectError|ConnectionRefused|Connection refused|ERR_CONNECTION|ConnectTimeout|ServiceRequestError"
)
TIMEOUT = re.compile(r"TimeoutError|Timeout \d+ms exceeded|waiting for (locator|get_by)")


def describe(item: pytest.Item) -> dict[str, Any]:
    """Where a test sits in the tree and what it is called, from its path and its docstring."""
    path = Path(str(item.path)).relative_to(item.config.rootpath).as_posix()
    parts = path.split("/")  # tests/<module>/<feature...>/<role>/<file>.py
    function = getattr(item, "obj", None)
    doc = (function.__doc__ or "").strip().splitlines() if function else []
    first = doc[0].strip() if doc else item.name
    match = TC_ID.match(first)
    known_bug = item.get_closest_marker("known_bug")
    nested = len(parts) > 3
    return {
        "nodeid": item.nodeid,
        "file": path,
        "module": parts[1] if nested else "",
        "feature": "/".join(parts[2:-2]),
        "role": parts[-2] if nested else "",
        "testCaseId": match.group(0) if match else None,
        "title": (first[match.end() :] if match else first).strip().rstrip("."),
        "markers": sorted({marker.name for marker in item.iter_markers()} & KNOWN_MARKERS),
        "knownBug": known_bug.args[0] if known_bug and known_bug.args else None,
        "line": (item.location[1] or 0) + 1,
    }


def error_type(call: pytest.CallInfo[None], when: str) -> str:
    """assertion, timeout, environment, code or setup; the dashboard turns it into a failure type."""
    excinfo = call.excinfo
    if excinfo is None:
        return "unknown"
    text = f"{excinfo.typename}: {excinfo.value}"
    if ENVIRONMENT.search(text):
        return "environment"
    if when != "call":
        return "setup"
    if excinfo.errisinstance(CODE_ERRORS):
        return "code"
    if TIMEOUT.search(text):
        return "timeout"
    return "assertion"


class StepRecorder:
    """Receives allure.step events and keeps the titles of the running test, marking the one that failed."""

    def __init__(self) -> None:
        self.steps: list[dict[str, Any]] = []
        self._open: dict[str, int] = {}

    def reset(self) -> None:
        self.steps, self._open = [], {}

    @allure_commons.hookimpl
    def start_step(self, uuid: str, title: str, params: Any) -> None:
        self._open[uuid] = len(self.steps)
        self.steps.append({"title": title, "failed": False})

    @allure_commons.hookimpl
    def stop_step(self, uuid: str, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        index = self._open.pop(uuid, None)
        if index is not None and exc_type is not None:
            self.steps[index]["failed"] = True


class DashboardReporter:
    def __init__(self, config: pytest.Config) -> None:
        self.config = config
        folder = config.getoption("--dashboard-dir")
        self.dir = Path(folder) if folder else None
        self.is_main = not hasattr(config, "workerinput")
        self.uses_xdist = config.pluginmanager.hasplugin("dsession")
        self.results: dict[str, dict[str, Any]] = {}
        self.attempts: dict[str, int] = {}
        self.started = time.time()
        self.start_sent = False
        self.steps = StepRecorder()
        allure_commons.plugin_manager.register(self.steps)
        if self.dir and self.is_main:
            self.dir.mkdir(parents=True, exist_ok=True)
            (self.dir / "progress.jsonl").write_text("", encoding="utf-8")

    def emit(self, event: dict[str, Any]) -> None:
        if self.dir and self.is_main:
            with (self.dir / "progress.jsonl").open("a", encoding="utf-8") as file:
                file.write(json.dumps({"t": round(time.time(), 3), **event}) + "\n")

    def emit_start(self, total: int) -> None:
        if not self.start_sent:
            self.start_sent = True
            self.emit({"event": "start", "total": total})

    # Collection

    def pytest_collection_finish(self, session: pytest.Session) -> None:
        catalog = self.config.getoption("--dashboard-catalog")
        if catalog and self.is_main:
            tests = [describe(item) for item in session.items]
            Path(catalog).write_text(json.dumps({"tests": tests}, indent=1), encoding="utf-8")
        if self.is_main and not self.uses_xdist:
            self.emit_start(len(session.items))

    @pytest.hookimpl(optionalhook=True)
    def pytest_xdist_node_collection_finished(self, node: Any, ids: list[str]) -> None:
        self.emit_start(len(ids))

    # Running: the process that runs the test attaches its details to the report

    def pytest_runtest_setup(self, item: pytest.Item) -> None:
        self.steps.reset()

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self, item: pytest.Item, call: pytest.CallInfo[None]):  # type: ignore[no-untyped-def]
        outcome = yield
        report: pytest.TestReport = outcome.get_result()
        details = describe(item)
        details["steps"] = list(self.steps.steps)
        if report.failed:
            details["errorType"] = error_type(call, report.when)
            details["errorMessage"] = short_message(call)
        report.user_properties.append(("dashboard", details))

    # Reporting: only the main process sees every report

    def pytest_runtest_logstart(self, nodeid: str, location: Any) -> None:
        self.emit({"event": "test_start", "nodeid": nodeid})

    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        if not self.is_main:
            return
        details: dict[str, Any] = dict(report.user_properties).get("dashboard", {})  # type: ignore[assignment]
        result = self.results.setdefault(report.nodeid, {**details, "outcome": "passed", "durationMs": 0})
        result["durationMs"] += int(report.duration * 1000)
        for key in ("errorType", "errorMessage", "steps"):
            if details.get(key):
                result[key] = details[key]

        if report.outcome == "rerun":
            self.attempts[report.nodeid] = self.attempts.get(report.nodeid, 1) + 1
            return
        if report.failed:
            result["outcome"] = "failed"
            result["phase"] = report.when
        elif report.skipped and report.when in ("setup", "call"):
            result["outcome"] = "skipped"
            result["errorMessage"] = skip_reason(report)

        finished = report.when == "teardown" or (report.when == "setup" and not report.passed)
        if finished:
            result["attempts"] = self.attempts.get(report.nodeid, 1)
            if result["outcome"] == "passed" and result["attempts"] > 1:
                result["outcome"] = "flaky"
            self.emit(
                {
                    "event": "test_end",
                    "nodeid": report.nodeid,
                    "outcome": result["outcome"],
                    "durationMs": result["durationMs"],
                }
            )

    def pytest_sessionfinish(self, session: pytest.Session, exitstatus: int) -> None:
        if not self.dir or not self.is_main:
            return
        artifacts = Path(str(self.config.getoption("--output", "test-results")))
        for result in self.results.values():
            result["media"] = media_for(result["nodeid"], artifacts, self.dir)
        report = {
            "startedAt": self.started,
            "finishedAt": time.time(),
            "exitStatus": int(exitstatus),
            "results": list(self.results.values()),
        }
        (self.dir / "report.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
        self.emit({"event": "finish", "exitStatus": int(exitstatus)})


def short_message(call: pytest.CallInfo[None]) -> str:
    if call.excinfo is None:
        return ""
    message = str(call.excinfo.value).strip() or call.excinfo.typename
    return message.split("\nassert ")[0][:2000]


def skip_reason(report: pytest.TestReport) -> str:
    longrepr = report.longrepr
    if isinstance(longrepr, tuple) and len(longrepr) == 3:
        return str(longrepr[2]).removeprefix("Skipped: ")
    return ""


def media_for(nodeid: str, artifacts: Path, base: Path) -> dict[str, Any]:
    """Screenshots, video and trace that pytest-playwright kept for this test (only on failure)."""
    function = nodeid.split("::")[-1].split("[")[0].replace("_", "-").lower()
    media: dict[str, Any] = {"screenshots": []}
    if not artifacts.is_dir():
        return media
    for folder in artifacts.iterdir():
        if not (folder.is_dir() and function in folder.name.lower()):
            continue
        for file in sorted(folder.rglob("*")):
            relative = relative_to(file, base)
            if file.suffix == ".png":
                media["screenshots"].append(relative)
            elif file.suffix == ".webm":
                media["video"] = relative
            elif file.name == "trace.zip":
                media["trace"] = relative
    return media


def relative_to(file: Path, base: Path) -> str:
    try:
        return file.resolve().relative_to(base.resolve()).as_posix()
    except ValueError:
        return file.resolve().as_posix()


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("dashboard", "QA Hub dashboard")
    group.addoption("--dashboard-dir", default=None, help="write progress.jsonl and report.json here")
    group.addoption("--dashboard-catalog", default=None, help="write the collected tests as JSON here")


def pytest_configure(config: pytest.Config) -> None:
    if config.getoption("--dashboard-dir") or config.getoption("--dashboard-catalog"):
        config.pluginmanager.register(DashboardReporter(config), "dashboard-reporter")
