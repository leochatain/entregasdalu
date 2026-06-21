# entregasdalu — compose "web" service (Django + gunicorn). Build context: ./backend
# "web" is the compose service name, not a web/ dir (CLAUDE.md). uv runs everything.
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

# Install deps first (cached layer) from the lockfile only, then the project.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY . .
RUN uv sync --frozen --no-dev

# Collect Django/allauth's own static (served by whitenoise). DEBUG defaults False;
# a throwaway key satisfies settings import at build time (real key comes from env).
RUN DJANGO_SECRET_KEY=build-only uv run python manage.py collectstatic --noinput

EXPOSE 8000

# Migrate (idempotent) then serve. 2 workers is ample for one user (design.md §7.1).
CMD ["sh", "-c", "uv run python manage.py migrate --noinput && \
  uv run gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2"]
