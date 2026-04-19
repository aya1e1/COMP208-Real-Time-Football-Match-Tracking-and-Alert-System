# VPS Deployment Guide

This project can be deployed on a VPS using:

- `venv` for Python dependencies
- `gunicorn` to run the Flask app
- `nginx` as the public web server and reverse proxy

This guide assumes:

- Fedora-based VPS
- Project path: `/srv/football-app`
- Public access by server IP, not a custom domain

## 1. Install system packages

```bash
sudo dnf install -y python3 python3-pip nginx git
sudo systemctl enable --now nginx
```

## 2. Copy the project to the VPS

If using Git:

```bash
cd /srv
sudo git clone <your-repo-url> football-app
sudo chown -R $USER:$USER /srv/football-app
cd /srv/football-app
```

## 3. Create the virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn
```

## 4. Create the environment file

Create a `.env` file in the project root:

Generate a strong `SECRET_KEY` with:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

```env
SECRET_KEY=some-long-random-string
API_FOOTBALL_KEY=your_api_key
API_FOOTBALL_BASE_URL=https://v3.football.api-sports.io
USE_MOCKS=false
```

## 5. Test the app with Gunicorn

Run this from the project root:

```bash
source venv/bin/activate
gunicorn -w 1 -b 127.0.0.1:8000 run:app
```

Then open another terminal and test:

```bash
curl http://127.0.0.1:8000/
```

Use only `-w 1` for now because this project uses SQLite and performs startup sync work when the app is created.

## 6. Enable the Nginx config

This repository includes:

- [`nginx.conf`](./nginx.conf)

On Fedora, it is simplest to place the site config under `/etc/nginx/conf.d/`:

```bash
sudo cp /srv/football-app/deployment/nginx.conf /etc/nginx/conf.d/football-app.conf
sudo nginx -t
sudo systemctl reload nginx
```

## 7. Open port 80

If using `firewalld`:

```bash
sudo systemctl enable --now firewalld
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --reload
```

If your VPS provider has a cloud firewall or security group, also allow inbound TCP on port `80`.

## 8. Visit the app

Open:

```text
http://YOUR_SERVER_IP/
```

## 9. Important notes

- Do not use `python run.py` in production.
- Use Gunicorn instead of Flask's built-in debug server.
- The app currently stores data in SQLite, so this setup is best as a single-instance deployment.
- The app also writes cached API JSON files, so the project directory must be writable by the app user.
- Fedora may enforce SELinux. If Nginx cannot connect to Gunicorn, you may need:

```bash
sudo setsebool -P httpd_can_network_connect 1
```

## 10. Create a systemd service for Gunicorn

Create a service file:

```bash
sudo nano /etc/systemd/system/football-app.service
```

Add:

```ini
[Unit]
Description=Gunicorn instance for football-app
After=network.target

[Service]
User=YOUR_USERNAME
Group=YOUR_USERNAME
WorkingDirectory=/srv/football-app
EnvironmentFile=/srv/football-app/.env
ExecStart=/srv/football-app/venv/bin/gunicorn -w 1 -b 127.0.0.1:8000 run:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Replace `YOUR_USERNAME` with your actual VPS username.

Then reload `systemd`, enable the service, and start it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now football-app
```

Check its status:

```bash
sudo systemctl status football-app
```

View logs:

```bash
sudo journalctl -u football-app -f
```

After that, Gunicorn will:

- start on boot
- restart automatically if it crashes
- run without keeping a terminal open
