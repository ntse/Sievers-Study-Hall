# Sievers Study Hall

Any question? https://substack.com/home/post/p-165326616

Any other question? sieversstudyhall@gmail.com

## Running with Docker

### Development

```bash
docker compose -f docker-compose.dev.yml up --build
```

App available at `http://localhost:5000` with auto-reload on code changes.

### Production

Create a `.env` file:
```bash
FLASK_SECRET_KEY=your-secure-key-here
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

Then run:
```bash
docker compose up --build
```

## Running tests

```bash
# With Docker
docker compose -f docker-compose.dev.yml exec app python -m pytest tests/

# Without Docker
python -m venv .venv
.venv/bin/pip install -r requirements.txt pytest
.venv/bin/python -m pytest tests/
```

### Browser end-to-end tests

```bash
.venv/bin/pip install -r requirements-e2e.txt
.venv/bin/python -m playwright install --with-deps chromium
.venv/bin/python -m pytest e2e/ -v --tracing retain-on-failure --screenshot only-on-failure
```

By default the suite builds and runs an isolated production container as its normal
non-root user, with a temporary account and database. Docker must be available.
The fixture initializes the database before starting the image's Gunicorn command
to avoid concurrent table creation on a fresh database. No local data is mounted;
the container is removed afterward. `E2E_IMAGE` selects an already built image.

To test a deployed site, pass its origin with `--base-url` or `E2E_BASE_URL`.
This mode uses only public browser flows, without Docker or server access:

```bash
# Read-only deployment checks; no account required
.venv/bin/python -m pytest e2e/ --base-url https://your-deployment.example -m smoke

# Full suite; set E2E_EMAIL and E2E_PASSWORD through your secret store/environment
.venv/bin/python -m pytest e2e/ --base-url https://your-deployment.example -v
```

Full deployed runs require an existing **dedicated test account**. Account tests
reset that account's selected exercise before and after each test, and restore
feedback settings. They create normal exercise analytics entries. Do not use a
personal account. Run sequentially and do not share the account between concurrent
runs. No accounts are created on deployed sites. Guest tests use a fresh browser
context for every test; missing account credentials fail account tests explicitly.

Coverage includes login/logout, invalid credentials, guest and signed-in exercise
completion, progress after reload and re-login, incorrect answers, resetting
progress, and feedback settings. `E2E_EXERCISE` selects a preposition-verb input
exercise (default: `19`). Run from the same source revision as the deployed site:
answers come from the checked-in exercise CSV, including randomized question IDs.
Use `-m 'not account'` for guest coverage without credentials and `--headed` to watch.

CI runs the full suite against the production build artifact. The reusable
`.github/workflows/e2e.yml` workflow also accepts `base-url`, `suite` (`smoke` or
`full`), and `exercise` inputs, with `E2E_EMAIL` / `E2E_PASSWORD` secrets. A future
CD job can call it after deployment; it can also be run manually today. Deployed
workflow runs against the same URL are serialized.

Failure screenshots/traces and local container logs go to `test-results/`; CI
retains them for seven days. Artifacts can include test-account credentials and
session data, so restrict their access as you would other CI secrets. Browser
JavaScript errors and same-origin server errors fail the tests automatically.
