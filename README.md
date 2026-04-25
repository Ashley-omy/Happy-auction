# Happy Auctions

Happy Auctions is a full-stack auction app built with Django (API) and React/Vite (SPA).

Deployment target for this repository:
- Backend: AWS EC2 (Gunicorn + Nginx)
- Frontend: AWS Amplify Hosting
- API connection: Frontend calls `https://api.your-domain.com/api`

## Project Structure

- `auctions/backend`: Django API
- `auctions/frontend`: React + Vite frontend
- `deploy/ec2`: EC2 deployment templates
- `amplify.yml`: Amplify build config (monorepo)

## Deployment-Oriented Changes Included

1. Frontend
- API base URL is configurable via `VITE_API_BASE_URL`
- Local development can still use Vite proxy (`/api -> http://127.0.0.1:8000`)

2. Backend
- `DEBUG`, `SECRET_KEY`, `ALLOWED_HOSTS`, `CORS`, and `CSRF` moved to environment variables
- Production cookie security is enabled when `DJANGO_DEBUG=False`
  - `SESSION_COOKIE_SECURE=True`
  - `CSRF_COOKIE_SECURE=True`
  - `SameSite=None` (required when frontend and backend are on different domains)
- `/` can redirect to `FRONTEND_URL`

3. Ops support files
- `auctions/backend/.env`
- `auctions/frontend/.env`
- `deploy/ec2/gunicorn.service`
- `deploy/ec2/nginx.conf`

## 1) Deploy Backend to EC2

Assumes Ubuntu 22.04.

### 1-1. Initial setup

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv nginx git
```

### 1-2. Clone and install

```bash
cd /home/ubuntu
git clone <YOUR_REPO_URL> 03commerce
cd 03commerce
python3 -m venv .venv
source .venv/bin/activate
pip install -r auctions/backend/requirements.txt
```

### 1-3. Configure backend env

```bash
nano auctions/backend/.env
```

Set at least these values:
- `DJANGO_SECRET_KEY`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_CORS_ALLOWED_ORIGINS`
- `DJANGO_CSRF_TRUSTED_ORIGINS`
- `DATABASE_URL`
- `FRONTEND_URL`

### 1-4. Migrate and collect static files

```bash
source .venv/bin/activate
cd auctions/backend
python manage.py migrate
python manage.py collectstatic --noinput
```

### 1-5. Run Gunicorn with systemd

```bash
sudo cp /home/ubuntu/03commerce/deploy/ec2/gunicorn.service /etc/systemd/system/gunicorn.service
sudo systemctl daemon-reload
sudo systemctl enable gunicorn
sudo systemctl start gunicorn
sudo systemctl status gunicorn
```

Update paths in `gunicorn.service` as needed.

### 1-6. Configure Nginx

```bash
sudo cp /home/ubuntu/03commerce/deploy/ec2/nginx.conf /etc/nginx/sites-available/auctions
sudo ln -s /etc/nginx/sites-available/auctions /etc/nginx/sites-enabled/auctions
sudo nginx -t
sudo systemctl restart nginx
```

Update `server_name` and `alias` paths in `nginx.conf`.

### 1-7. Enable HTTPS (recommended)

HTTPS is required for secure cross-site cookies in production.

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d api.your-domain.com
```

## 2) Deploy Frontend to Amplify

### 2-1. Connect repository

- Connect this repository in AWS Amplify Hosting
- Use `amplify.yml` in repository root
- Monorepo `appRoot`: `auctions/frontend`

### 2-2. Set environment variable

In Amplify Environment variables:
- `VITE_API_BASE_URL=https://api.your-domain.com/api`

### 2-3. Add SPA rewrite rule

Amplify Console > Rewrites and redirects:
- Source: `/<*>`
- Target: `/index.html`
- Type: `200 (Rewrite)`

This prevents 404 on direct page access like `/auction/1`.

## 3) Verification Checklist

1. Open the Amplify URL
2. Confirm API requests go to `https://api.your-domain.com/api/...`
3. Confirm no CORS errors
4. Confirm `sessionid` and `csrftoken` cookies are issued with `Secure`
5. Confirm create bid/comment/listing flows work

## Local Development

### Backend

```bash
cd auctions/backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Frontend

```bash
cd auctions/frontend
npm ci
npm run dev
```

Local dev uses Vite proxy: `/api -> http://127.0.0.1:8000`.
