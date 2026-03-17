
# Real Time Football Match Tracking and Alert System

> COMP208 Group Software Project - Universiti of Liverpool 2025/2026
>
> Team: Hamza Al Zudi Garcia-Olalla . Ziad Azmi . Ziad Azmi . Balqis Binti Abdul Halim . Best Boonthanomwong . Jacob Daya . Aya El Khayat . Tom Sutton

## About

A real- time football match tracking and alert system that provides live scores, match events (goals, cards, substitutions), league standings, player statistics, and personalised notification for registered users.

**Tech stack:** Python . Flask . SQLite . HTML/CSS . API-Football

---

## Features

- 🔴Live match scores updated every 30 seconds
- ⚽Match events timeline (goals, cards, substitutions)
- 🏆Premier League statndings table
- 👤User accounts with personalised team alerts
- 📊Player and team statistics
- 💾 API caching system to stay witnin rate limits

---

## Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_ORG/COMP208-Real-Time-Football-Match-Tracking-and-Alert-System
cd COMP208-Real-Time-Football-Match-Tracking-and-Alert-System
```

### 2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
### 3. Add API key
```bash
cp .env.example .env
```

### 4. Run the app
```bash
python run.py
# Visit http://localhost:5000
```

---

## Project Structure
```
├── backend/
│   ├── app.py              # Flask application factory
│   ├── api/
│   │   ├── football_api.py # API-Football
│   │   └── cache.py        # SQLite-backed cache
│   ├── db/
│   │   └── database.py     # Database helpers
│   ├── events/
│   │   ├── processor.py    # Match event processor
│   │   └── notifier.py     # User notification engine
│   └── routes/             # Flask blueprints
├── database/
│   └── schema.sql          # Full database schema
├── frontend/
│   ├── templates/          # HTML templates
│   └── static/css/         # Stylesheet
├── tests/
│   └── test_all.py         # Unit and integration tests
└── .github/workflows/
    └── ci.yml              # GitHub Actions CI/CD
```

---

## Running Tests
```bash
python -m unittest tests.test_all -v
```

---

## API

---

## Contributors
| Name | Role | GitHub |
|------|------|--------|
| Jacob Daya | ... | @kedachii |
| Aya El Khayat | ... | @aya1e1 |
| Tom Sutton | ... | @Thomas-Sutton-0 |
| Best Boonthanomwong | ... | @nongbed |
| Hamza Al Zudi Garcia-Olalla | ... | HAZ-GO |
| Balqis Binti Abdul Halim | ... | balqishalim |
| Ziad Azmi | ... | ziad-304 |

---
## Run
1. Create virtual environment 
`python -m venv venv` 
2. Activate virtual environment
`source venv/bin/activate`
3. Install requirements
`pip install -r requirements.txt`
