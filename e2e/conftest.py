import csv
import json
import os
import secrets
import subprocess
import time
import uuid
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import urlopen

import pytest

ROOT = Path(__file__).resolve().parents[1]


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "smoke: read-only checks suitable for any deployment"
    )
    config.addinivalue_line(
        "markers", "account: requires a dedicated E2E account on deployed sites"
    )


def docker(*args, **kwargs):
    result = subprocess.run(
        ["docker", *args],
        check=False,
        text=True,
        capture_output=True,
        timeout=180,
        **kwargs,
    )
    if result.returncode:
        pytest.fail(f"Docker {args[0]} failed:\n{result.stderr}", pytrace=False)
    return result.stdout.strip()


@pytest.fixture(scope="session")
def target_url(pytestconfig):
    url = pytestconfig.getoption("base_url") or os.environ.get("E2E_BASE_URL")
    if url:
        parsed = urlsplit(url)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.netloc
            or parsed.path not in {"", "/"}
        ):
            pytest.fail("E2E base URL must be an HTTP(S) origin without a path")
        return url.rstrip("/")
    return None


@pytest.fixture(scope="session")
def credentials(target_url):
    if target_url:
        email, password = os.environ.get("E2E_EMAIL"), os.environ.get("E2E_PASSWORD")
        if not email or not password:
            pytest.fail(
                "Account tests require E2E_EMAIL and E2E_PASSWORD for a dedicated test account"
            )
        return email, password
    return "learner@example.test", secrets.token_urlsafe(24)


@pytest.fixture(scope="session")
def production_app(credentials, pytestconfig):
    image = os.environ.get("E2E_IMAGE", "sievers-study-hall-e2e")
    if not os.environ.get("E2E_IMAGE"):
        docker("build", "--target", "production", "-t", image, str(ROOT))
    name = f"study-hall-e2e-{uuid.uuid4().hex[:12]}"
    command = json.loads(
        docker("image", "inspect", "--format", "{{json .Config.Cmd}}", image)
    )
    # Initialize the fresh database before concurrent Gunicorn workers start.
    setup = """
import os
from app import app
from users.users.models import User, db
with app.app_context():
    user = User(email=os.environ["E2E_EMAIL"])
    user.set_password(os.environ["E2E_PASSWORD"])
    db.session.add(user)
    db.session.commit()
"""
    env = {
        **os.environ,
        "E2E_EMAIL": credentials[0],
        "E2E_PASSWORD": credentials[1],
        "FLASK_SECRET_KEY": secrets.token_hex(32),
    }
    started = False
    try:
        docker(
            "run",
            "-d",
            "--name",
            name,
            "-p",
            "127.0.0.1::5000",
            "-e",
            "FLASK_ENV=production",
            "-e",
            "FLASK_SECRET_KEY",
            "-e",
            "E2E_EMAIL",
            "-e",
            "E2E_PASSWORD",
            image,
            "sh",
            "-c",
            'python -c "$1" && shift && exec "$@"',
            "e2e-start",
            setup,
            *command,
            env=env,
        )
        started = True
        port = docker("port", name, "5000/tcp").rsplit(":", 1)[1]
        url = f"http://127.0.0.1:{port}"
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            try:
                with urlopen(url, timeout=1) as response:
                    if response.status == 200:
                        break
            except (URLError, TimeoutError, ConnectionError):
                pass
            time.sleep(0.5)
        else:
            pytest.fail(
                "Production container failed to become ready; see container.log"
            )
        yield url
    finally:
        if started:
            artifacts = Path(pytestconfig.getoption("output"))
            artifacts.mkdir(parents=True, exist_ok=True)
            result = subprocess.run(
                ["docker", "logs", name],
                check=False,
                capture_output=True,
                text=True,
                timeout=15,
            )
            (artifacts / "container.log").write_text(result.stdout + result.stderr)
            docker("rm", "-f", name)


@pytest.fixture(scope="session")
def base_url(target_url, request):
    return target_url or request.getfixturevalue("production_app")


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args, base_url):
    return {**browser_context_args, "base_url": base_url, "locale": "en-GB"}


@pytest.fixture(autouse=True)
def browser_errors(page, base_url):
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on(
        "response",
        lambda response: (
            errors.append(f"HTTP {response.status}: {response.url}")
            if response.url.startswith(base_url + "/") and response.status >= 500
            else None
        ),
    )
    yield
    assert not errors, "Browser errors:\n" + "\n".join(errors)


@pytest.fixture(scope="session")
def exercise():
    number = int(os.environ.get("E2E_EXERCISE", "19"))
    path = ROOT / "data/datasets/praepositionen/praepositionen_verben.csv"
    with path.open() as source:
        answers = {
            str(index): row["answer"].split("/")[0]
            for index, row in enumerate(csv.DictReader(source), 1)
            if int(row["exercise"]) == number
        }
    assert answers, f"No test answers for exercise {number}"
    return {
        "path": f"/unit/praepositionen_verben/exercise/{number}",
        "answers": answers,
    }


@pytest.fixture
def signed_in(page, credentials, base_url):
    from e2e.journeys import sign_in

    sign_in(page, credentials, base_url)
    return page


@pytest.fixture
def clean_account_exercise(signed_in, exercise):
    from e2e.journeys import reset_exercise

    reset_exercise(signed_in, exercise)
    yield
    reset_exercise(signed_in, exercise)


@pytest.fixture
def feedback_enabled(page):
    from e2e.journeys import set_feedback

    original = set_feedback(page, True)
    yield
    set_feedback(page, original)
