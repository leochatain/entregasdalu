# Deploying entregasdalu

A toy for one user: the entire deploy is `docker compose up -d --build` on a single
small host. Two containers — `caddy` (TLS + SPA + reverse proxy) and `web` (Django +
gunicorn) — read config from a repo-root `.env`. SQLite + photos are host bind-mounts.

> **Backups:** none, by decision (spec §3.4). The diary lives in `./data/app.db`, a
> plain visible file on the host — `cp ./data/app.db ~/app.db.bak` is the manual rescue.
> Photos are reproducible from your originals; only `app.db` is irreplaceable.

## What runs where

| Path | Served by |
|---|---|
| `/api/*`, `/accounts/*` | `web` (Django-Ninja + allauth) via Caddy proxy |
| `/photos/*` | `web` (downscaling resize view) via Caddy proxy |
| everything else | the Vite SPA baked into the `caddy` image (`index.html` fallback) |

## One-time setup (manual — these can't be scripted from the repo)

### 1. Google OAuth client
In [Google Cloud Console](https://console.cloud.google.com/) → APIs & Services →
Credentials → **Create OAuth client ID** (type: Web application):
- Authorized redirect URI: `https://YOUR_DOMAIN/accounts/google/login/callback/`
- Copy the **Client ID** and **Client secret** into the server `.env`
  (`GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET`).

### 2. Lightsail instance
- Create the smallest Lightsail instance (Ubuntu).
- Install Docker + the compose plugin.
- In the Lightsail **networking** tab, open inbound **80** and **443**.
- Attach a **static IP**.

### 3. DNS
Point an **A record** for `YOUR_DOMAIN` at the Lightsail static IP. Caddy will
provision a Let's Encrypt certificate automatically on first start.

## First deploy

```bash
git clone <repo> entregasdalu && cd entregasdalu

# Create the production .env (copy the template, fill the prod block).
cp .env.example .env
#  set: DEBUG=False, DJANGO_SECRET_KEY=<long random>, ALLOWED_EMAILS,
#       DOMAIN, DJANGO_ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS=https://DOMAIN,
#       PHOTOS_ROOT=/srv/photos, DATABASE_PATH=/data/app.db, THUMBS_ROOT=/data/thumbs,
#       GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
#  ensure DEV_LOGIN_ENABLED is unset/False (settings refuses DEV_LOGIN with DEBUG=False).

# Generate a secret key, e.g.:
#   python3 -c "import secrets; print(secrets.token_urlsafe(64))"

# Drop curated photos into the tier folders (add-only; never rename a won photo).
#   photos/{rascunho,capitulo,tese}/<your-images>

make deploy        # docker compose up -d --build  (migrate runs on web start)
```

### 4. Point allauth at your domain (one-time, after the first `migrate`)
allauth builds OAuth callback URLs from the Django `Site` row (id=1, `SITE_ID=1`).
Set it to your domain once:

```bash
docker compose exec web uv run python manage.py shell -c \
  "from django.contrib.sites.models import Site; \
   s=Site.objects.get(pk=1); s.domain='YOUR_DOMAIN'; s.name='entregasdalu'; s.save()"
```

Then browse to `https://YOUR_DOMAIN`, sign in with an allowlisted Google account, and
the daily loop is live.

## Operating

```bash
make logs     # follow both services
make ps       # status
make deploy   # redeploy after a git pull (rebuilds images, re-runs migrate)
make down     # stop
```

- **New photos:** drop files into `photos/<tier>/` on the host — no restart needed
  (the offer reads the folder live; the resize view caches derivatives on first hit).
- **Updating code:** `git pull && make deploy`.
- **Manual backup:** `cp ./data/app.db ./data/app.db.$(date +%F).bak`.

## Local smoke test of the prod stack (optional, no real domain)

Run Caddy against `localhost` (internal CA) to exercise the container path before
shipping:

```bash
# Minimal .env: DEBUG=False, DJANGO_SECRET_KEY=test, ALLOWED_EMAILS=you@x.com,
#   DOMAIN=localhost, DJANGO_ALLOWED_HOSTS=localhost,
#   CSRF_TRUSTED_ORIGINS=https://localhost, PHOTOS_ROOT=/srv/photos,
#   DATABASE_PATH=/data/app.db, THUMBS_ROOT=/data/thumbs
make deploy
curl -k https://localhost/api/config            # {"devLogin": false}
curl -k -o /dev/null -w '%{size_download}\n' https://localhost/photos/<tier>/<file>
#   ^ should be ~100-300 KB (downscaled), not the multi-MB original
```
