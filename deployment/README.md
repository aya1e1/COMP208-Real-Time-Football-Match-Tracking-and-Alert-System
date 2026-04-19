
# VPS Deployment Guide

  

This project can be deployed on a VPS using:

  

-  `venv` for Python dependencies

-  `gunicorn` to run the Flask app

-  `nginx` as the public web server and reverse proxy

  

This guide assumes:

  

- Fedora-based VPS

- Project path: `/srv/football-app`

- Public access by server IP, not a custom domain

  

## 1. Install system packages

  

```bash

sudo  dnf  install  -y  python3  python3-pip  nginx  git

sudo  systemctl  enable  --now  nginx

```

  

## 2. Copy the project to the VPS

  

If using Git:

  

```bash

cd  /srv

sudo  git  clone <your-repo-url> football-app

sudo  chown  -R  $USER:$USER  /srv/football-app

cd  /srv/football-app

```

  

## 3. Create the virtual environment

  

```bash

python3  -m  venv  venv

source  venv/bin/activate

pip  install  --upgrade  pip

pip  install  -r  requirements.txt

pip  install  gunicorn

```

  

## 4. Create the environment file

  

Create a `.env` file in the project root:

  

Generate a strong `SECRET_KEY` with:

  

```bash

python3  -c  "import secrets; print(secrets.token_hex(32))"

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

source  venv/bin/activate

gunicorn  -w  1  -b  127.0.0.1:8000  run:app

```

  

Then open another terminal and test:

  

```bash

curl  http://127.0.0.1:8000/

```

  

Use only `-w 1` for now because this project uses SQLite and performs startup sync work when the app is created.

  

## 6. Enable the Nginx config

  

This repository includes:

  

- [`nginx.conf`](./nginx.conf)

  

On Fedora, it is simplest to place the site config under `/etc/nginx/conf.d/`:

  

```bash

sudo  cp  /srv/football-app/deployment/nginx.conf  /etc/nginx/conf.d/football-app.conf

sudo  nginx  -t

sudo  systemctl  reload  nginx

```

  




  

## 8. Visit the app

  

Open:

  

```text

http://YOUR_SERVER_IP/

```

  


```

  

## 10. Create a systemd service for Gunicorn

  

Create a service file:

  

```bash

sudo  nano  /etc/systemd/system/football-app.service

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

sudo  systemctl  daemon-reload

sudo  systemctl  enable  --now  football-app

```

  

Check its status:

  

```bash

sudo  systemctl  status  football-app

```
  

View logs:


```bash

sudo  journalctl  -u  football-app  -f

```


After that, Gunicorn will:

- start on boot

- restart automatically if it crashes

- run without keeping a terminal open

## 11. Automate deployment from GitHub to the VPS

This repository includes a GitHub Actions workflow at:

- [`.github/workflows/deploy.yml`](../.github/workflows/deploy.yml)

It is set to deploy automatically when a commit is pushed to the `main` branch.

### GitHub secrets

In your GitHub repository, open:

`Settings -> Secrets and variables -> Actions`

Create these repository secrets:

- `VPS_HOST` . your server IP or hostname
- `VPS_USER` . the Linux user GitHub Actions should log in as
- `VPS_PASSWORD` . the SSH password for that user
- `VPS_PORT` . optional, only needed if SSH is not on port `22`

### How the deploy workflow works

On each push to `main`, GitHub Actions will:

1. run the backend tests
2. connect to the VPS over SSH
3. update `/srv/football-app` to the latest `origin/main`
4. install any updated Python dependencies
5. restart the `football-app` service

The deploy step runs these commands on the VPS:

```bash
cd /srv/football-app
git fetch origin
git reset --hard origin/main
source venv/bin/activate
pip install -r requirements.txt
test -x /srv/football-app/venv/bin/gunicorn
sudo systemctl restart football-app
sudo systemctl status football-app --no-pager
```

### Important `sudo` note

If the VPS user needs a password every time `sudo` is used, the deployment can fail because GitHub Actions cannot answer an interactive `sudo` prompt.

The simplest fix is to allow this user to restart the service without a `sudo` password.

Run:

```bash
sudo visudo
```

Add a line like this, replacing `YOUR_USERNAME` with the VPS username:

```sudoers
YOUR_USERNAME ALL=(ALL) NOPASSWD: /bin/systemctl restart football-app, /bin/systemctl status football-app
```

If your system uses a different `systemctl` path, check it with:

```bash
which systemctl
```

### First deployment checklist

Before enabling automatic deployment, make sure:

- the project is already cloned to `/srv/football-app`
- the virtual environment exists at `/srv/football-app/venv`
- the `.env` file exists on the VPS
- `sudo systemctl status football-app` works on the server
- the GitHub repository on the VPS points to the correct remote

## 12. Troubleshooting `football-app.service`

If `sudo systemctl status football-app` shows:

```text
Active: failed (Result: resources)
```

that usually means `systemd` could not launch the Gunicorn process at all. In this setup, the two most likely causes are:

- `User=` or `Group=` in `/etc/systemd/system/football-app.service` still contains `YOUR_USERNAME` or another invalid account
- `/srv/football-app/venv/bin/gunicorn` does not exist because Gunicorn was not installed into the virtual environment

Run these checks on the VPS:

```bash
sudo systemctl cat football-app
id YOUR_USERNAME
ls -l /srv/football-app/venv/bin/gunicorn
sudo journalctl -u football-app -n 50 --no-pager
```

What to fix:

- if `User=` or `Group=` is wrong, edit the service and replace it with the real VPS username, then run `sudo systemctl daemon-reload`
- if the Gunicorn binary is missing, activate the venv and run `pip install -r requirements.txt`
- if the `.env` file is missing, recreate `/srv/football-app/.env` before restarting the service

Then restart and recheck:

```bash
sudo systemctl restart football-app
sudo systemctl status football-app --no-pager
```

### Security note

Password-based SSH automation works, but using an SSH key is usually more secure and easier to maintain long term.
