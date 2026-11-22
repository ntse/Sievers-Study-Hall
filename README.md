# Sievers Study Hall

Any question? https://substack.com/home/post/p-165326616

Any other question? sieversstudyhall@gmail.com

## Running with Docker
### Development

```bash
docker compose -f docker-compose.dev.yml up --build
```

Open `http://localhost:5000`. Includes Postgres and automatic code reload.

### Production

Create a `.env` file:

```dotenv
FLASK_SECRET_KEY=your-secure-key-here
POSTGRES_PASSWORD=replace-with-a-strong-password
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

```bash
docker compose up --build
```

The app builds its database URI from `POSTGRES_HOST`, `POSTGRES_PORT`,
`POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB`. `DATABASE_URL` overrides these.
