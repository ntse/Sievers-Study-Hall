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
.venv/bin/python -m pytest e2e/ --base-url http://127.0.0.1:5000 -m smoke

# Full suite; set E2E_EMAIL and E2E_PASSWORD through your secret store/environment
.venv/bin/python -m pytest e2e/ --base-url http://127.0.0.1:5000 -v
```
