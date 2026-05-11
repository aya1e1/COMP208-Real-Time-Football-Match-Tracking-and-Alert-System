# Real-Time Football Match Tracking and Alert System

COMP208 Group Software Project - University of Liverpool 2025/2026

Team: Hamza Al Zudi Garcia-Olalla, Ziad Azmi, Balqis Binti Abdul Halim, Best Boonthanomwong, Jacob Daya, Aya El Khayat, Tom Sutton

## Demo

https://vps-eaa16051.vps.ovh.net/

## About

This project is a real-time football match tracking and alert system. It provides live scores, match events, league standings, player statistics, and personalised notifications for registered users.

**Tech stack:** Python, Flask, SQLite, HTML/CSS, API-Football

## Features

- Match event timelines for goals, cards, and substitutions
- League standing tables
- Team statistics
- User accounts with the ability to favoruite teams
- Voting on fixture events
- Caching of data fetched from the exterrnal API

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/aya1e1/COMP208-Real-Time-Football-Match-Tracking-and-Alert-System
cd COMP208-Real-Time-Football-Match-Tracking-and-Alert-System
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate    # Mac/Linux
venv\Scripts\activate       # Windows
pip install -r requirements.txt
```

### 3. Create an environment file

```bash
cp .env.example .env
```

Open the new `.env` file in a text editor and update the values:

```text
API_FOOTBALL_KEY=your_api_football_key_here
USE_MOCKS=true
SECRET_KEY=your_secret_key_here
FLASK_ENV=development
```

| Variable | Required | Description |
|----------|----------|-------------|
| API_FOOTBALL_KEY | Yes for live API | API-Football key |
| API_FOOTBALL_BASE_URL | Yes for live API | API-Football base URL |
| USE_MOCKS | No | Use mock data instead of live API |
| SECRET_KEY | Yes | Flask session secret |
| FLASK_ENV | No | Flask environment |


### 4. Run the app locally

```bash
python run.py
```

Visit `http://localhost:5000` in your browser.

## Project Structure

```text
.
|-- backend/              # Flask app, routes, API integration, data sync
|-- database/             # SQLite schema and database files
|-- frontend/             # HTML templates and static assets
|-- tests/                # Unit and integration tests
|-- deployment/           # Deployment notes and server configuration
|-- run.py                # App entry point
|-- requirements.txt      # Python dependencies
`-- README.md             # Project documentation

## Running Tests

```bash
python -m unittest tests.test_all -v
```

## API

This project uses [API-Football v3](https://www.api-football.com/) on the free tier, which allows 100 requests per day.

Endpoints used:

- `/fixtures` - today's matches and live scores
- `/fixtures/events` - goals, cards, and substitutions
- `/standings` - league tables
- `/teams` - team information
- `/players` - player statistics

All API responses are cached in SQLite to stay within the free tier limit.

## Contributors

| Name | Role | GitHub |
|------|------|--------|
| Hamza Al Zudi Garcia-Olalla | Frontend | @HAZ-GO |
| Ziad Azmi | Backend & Frontend | @ziad-304 |
| Balqis Binti Abdul Halim | Database & Backend | @balqishalim |
| Best Boonthanomwong | Frontend | @nongbed |
| Jacob Daya | Database, Testing & Backend | @kedachii |
| Aya El Khayat | API Integration, Database, Testing, DevOps | @aya1e1 |
| Tom Sutton | Backend | @Thomas-Sutton-0 |
