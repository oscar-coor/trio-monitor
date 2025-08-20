# DEPLOYMENT – Ubuntu (systemd + Nginx)

Snabbguide för drift av Trio Monitor på Ubuntu med Uvicorn bakom Nginx. Förutsätter att backend körs på 127.0.0.1:8000 och frontend statiskt via Nginx.

## Förutsättningar
- Ubuntu 22.04+ (eller 24.04)
- Python 3.12+
- Node.js 18+ (för att bygga frontend)
- Nginx
- Certbot (valfritt, för HTTPS)

## Kataloger (rekommenderat)
- Kod: `/opt/trio-monitor` (git clone)
- Backend env: `/etc/trio-monitor/backend.env`
- Frontend build: `/var/www/trio-monitor`

## 1) Klona repo och installera backend
```bash
sudo mkdir -p /opt/trio-monitor /etc/trio-monitor /var/www/trio-monitor
sudo chown -R $USER:$USER /opt/trio-monitor /var/www/trio-monitor
cd /opt/trio-monitor
# git clone <REPO_URL> .   # Om repo inte redan finns
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r backend/requirements.txt
```

Skapa `/etc/trio-monitor/backend.env` (justera värden):
```env
TRIO_API_BASE_URL=https://<trio-api-host>
TRIO_USERNAME=
TRIO_PASSWORD=
TRIO_TOKEN=

DATABASE_URL=sqlite:///./db.sqlite
POLLING_INTERVAL=10
QUEUE_TIME_LIMIT=20
WARNING_THRESHOLD=18
SERVICE_LEVEL_TARGET=80

# CORS / Frontend
FRONTEND_URL=https://trio.example.com
ALLOWED_ORIGINS=https://trio.example.com

# Säkerhet
SECRET_KEY=change_me
PASSWORD_SALT=change_me
ENABLE_HTTPS=true
```

## 2) systemd-tjänst för backend
Skapa `/etc/systemd/system/trio-backend.service`:
```ini
[Unit]
Description=Trio Monitor Backend (Uvicorn)
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/trio-monitor
EnvironmentFile=/etc/trio-monitor/backend.env
ExecStart=/opt/trio-monitor/.venv/bin/python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000 --proxy-headers
Restart=always
User=www-data
Group=www-data

[Install]
WantedBy=multi-user.target
```

Aktivera och starta:
```bash
sudo systemctl daemon-reload
sudo systemctl enable trio-backend
sudo systemctl start trio-backend
sudo systemctl status trio-backend -n 50
```

Loggar:
```bash
journalctl -u trio-backend -f
```

## 3) Bygg och publicera frontend
```bash
cd /opt/trio-monitor/frontend
npm ci
npm run build
sudo rsync -a --delete build/ /var/www/trio-monitor/
```

 

## 4) Nginx-konfiguration
Skapa t.ex. `/etc/nginx/sites-available/trio-monitor.conf`:
```nginx
server {
    listen 80;
    server_name trio.example.com;

    # HTTP -> HTTPS (valfritt, om du använder TLS)
    # return 301 https://$host$request_uri;

    root /var/www/trio-monitor;
    index index.html;

    location / {
        try_files $uri /index.html;
    }

    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Aktivera och ladda om Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/trio-monitor.conf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 5) HTTPS med certbot (valfritt)
```bash
sudo apt-get update && sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d trio.example.com
```

## 6) Hälsokontroll och felsökning
- Testa `https://trio.example.com/` (frontend)
- Testa `https://trio.example.com/health` (backend)
- Om frontend visar proxy-fel: kontrollera att `trio-backend` kör och att Nginx proxar `/api` och `/health` korrekt
- Loggar: `journalctl -u trio-backend -n 200 -f` och `sudo tail -f /var/log/nginx/access.log /var/log/nginx/error.log`

## 7) Uppdateringar (deploy)
```bash
cd /opt/trio-monitor
sudo -u www-data git pull
/opt/trio-monitor/.venv/bin/pip install -r backend/requirements.txt
cd frontend && npm ci && npm run build
sudo rsync -a --delete build/ /var/www/trio-monitor/
sudo systemctl restart trio-backend
```

## 8) Säkerhets- och prestandatips
- Begränsa CORS till kända ursprung (`FRONTEND_URL`/`ALLOWED_ORIGINS`)
- Använd `SecretStr`/miljövariabler – lagra inga hemligheter i DB
- Polling 10 s, cache TTL <5 s för att spara Trio API
- Övervaka med `journalctl` och tänk på rate limits/retries
- Håll OS och beroenden uppdaterade
