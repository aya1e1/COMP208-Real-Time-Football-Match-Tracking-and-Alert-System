## Base URL

- API routes: `/api/...`
- Auth routes: `/auth/...`

Example local base URL:

```text
http://127.0.0.1:5000
```

## Authentication

Session-based authentication with Flask-Login.

- Public endpoints can be called without logging in.
- User-specific endpoints under `/api/me/...` require a logged-in session.
- After logging in, the browser or API client must keep the session cookie for future authenticated requests.

JSON auth endpoints:

- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/logout`

These routes return JSON when you send a JSON request body.

Example register request:

```json
{
  "username": "testuser",
  "email": "test@example.com",
  "password": "password123"
}
```

Example login request:

```json
{
  "username": "testuser",
  "password": "password123"
}
```

Successful auth response:

```json
{
  "user": {
    "UserID": 1,
    "Username": "testuser",
    "Email": "test@example.com",
    "CreatedDate": "2026-04-16 12:00:00"
  }
}
```

## Endpoints

### `GET /api/me`

Returns the currently authenticated user.

Auth required: yes

Response:

```json
{
  "user": {
    "UserID": 1,
    "Username": "testuser",
    "Email": "test@example.com",
    "CreatedDate": "2026-04-16 12:00:00"
  }
}
```

### `GET /api/me/favourite-teams`

Returns the logged-in user's favourite teams.

Auth required: yes

Response:

```json
{
  "data": [
    {
      "FavouriteTeamID": 1,
      "UserID": 1,
      "TeamID": 41,
      "CreatedDate": "2026-04-16 12:00:00",
      "Name": "Southampton",
      "Abbreviation": "SOU",
      "LogoURL": "https://...",
      "City": "Southampton",
      "Stadium": "St. Mary's Stadium"
    }
  ]
}
```

### `POST /api/me/favourite-teams`

Adds a team to the logged-in user's favourites.

Auth required: yes

Request body:

```json
{
  "team_id": 41
}
```

Success response:

```json
{
  "success": true
}
```

Status codes:

- `201` when added
- `400` if `team_id` is missing, not an integer, or the insert fails

### `DELETE /api/me/favourite-teams/<team_id>`

Removes a team from the logged-in user's favourites.

Auth required: yes

Success response:

```json
{
  "success": true
}
```

### `GET /api/me/favourite-players`

Returns the logged-in user's favourite players.

Auth required: yes

Response:

```json
{
  "data": [
    {
      "FavouritePlayerID": 1,
      "UserID": 1,
      "PlayerID": 138908,
      "CreatedDate": "2026-04-16 12:00:00",
      "FirstName": "Erling",
      "LastName": "Haaland",
      "Name": "E. Haaland",
      "MainPosition": "Attacker",
      "Nationality": "Norway"
    }
  ]
}
```

### `POST /api/me/favourite-players`

Adds a player to the logged-in user's favourites.

Auth required: yes

Request body:

```json
{
  "player_id": 138908
}
```

Success response:

```json
{
  "success": true
}
```

Status codes:

- `201` when added
- `400` if `player_id` is missing, not an integer, or the insert fails

### `DELETE /api/me/favourite-players/<player_id>`

Removes a player from the logged-in user's favourites.

Auth required: yes

Success response:

```json
{
  "success": true
}
```

### `GET /api/me/notification-preferences`

Returns the logged-in user's notification preferences.

Auth required: yes

Response:

```json
{
  "data": [
    {
      "PreferenceID": 1,
      "UserID": 1,
      "TeamID": 41,
      "NotifyGoals": 1,
      "NotifyCards": 1,
      "NotifySubstitutions": 0,
      "TeamName": "Southampton"
    }
  ]
}
```

Notes:

- `TeamID: null` means a global/default preference.
- Boolean-like values are stored and returned as `0` or `1`.

### `PUT /api/me/notification-preferences`

Creates or updates a notification preference for the logged-in user.

Auth required: yes

Request body:

```json
{
  "team_id": 41,
  "notify_goals": true,
  "notify_cards": true,
  "notify_substitutions": false
}
```

You can omit `team_id` or send it as `null`/`""` to update the global preference instead of a team-specific one.

Success response:

```json
{
  "data": {
    "PreferenceID": 1,
    "UserID": 1,
    "TeamID": 41,
    "NotifyGoals": 1,
    "NotifyCards": 1,
    "NotifySubstitutions": 0
  }
}
```

Status codes:

- `200` when updated
- `400` if `team_id` is provided but is not an integer

### `GET /api/leagues`

Returns all leagues currently stored in the database.

Auth required: no

Response:

```json
[
  {
    "LeagueID": 39,
    "Name": "Premier League"
  }
]
```

### `GET /api/leagues/<league_id>/teams`

Returns league details and the teams recorded for that league.

Auth required: no

Response:

```json
{
  "league": {
    "LeagueID": 39,
    "Name": "Premier League"
  },
  "teams": [
    {
      "TeamID": 41,
      "Name": "Southampton",
      "Abbreviation": "SOU",
      "City": "Southampton",
      "Stadium": "St. Mary's Stadium"
    }
  ]
}
```

Status codes:

- `200` on success
- `404` if the league is not found

### `GET /api/fixtures`

Returns fixtures from the database.

Auth required: no

Query parameters:

- `start_date` optional, format `YYYY-MM-DD`
- `end_date` optional, format `YYYY-MM-DD`

Examples:

```text
GET /api/fixtures
GET /api/fixtures?start_date=2026-04-01&end_date=2026-04-30
```

Behaviour:

- If no dates are provided, the endpoint returns the latest 10 fixtures ordered by match date descending.
- If dates are provided, all matching fixtures in the range are returned.

Response:

```json
[
  {
    "FixtureID": 1208399,
    "LeagueID": 39,
    "LeagueName": "Premier League",
    "Year": 2024,
    "HomeTeamID": 41,
    "HomeTeam": "Southampton",
    "HomeTeamAbbreviation": "SOU",
    "HomeTeamLogoURL": "https://...",
    "AwayTeamID": 50,
    "AwayTeam": "Manchester City",
    "AwayTeamAbbreviation": "MCI",
    "AwayTeamLogoURL": "https://...",
    "Location": "St. Mary's Stadium",
    "MatchDate": "2026-04-16 15:00:00",
    "HomeScore": 1,
    "AwayScore": 3,
    "Status": "FT",
    "Elapsed": 90
  }
]
```

Status codes:

- `200` on success
- `400` if a date format is invalid
- `400` if `start_date` is later than `end_date`

### `GET /api/fixtures/<fixture_id>`

Returns a detailed fixture payload including match info, events, statistics, venue-based team form, and head-to-head history.

Auth required: no

Response shape:

```json
{
  "data": [
    {
      "FixtureID": 1208399,
      "LeagueID": 39,
      "LeagueName": "Premier League",
      "Year": 2024,
      "HomeTeamID": 41,
      "HomeTeam": "Southampton",
      "AwayTeamID": 50,
      "AwayTeam": "Manchester City",
      "Location": "St. Mary's Stadium",
      "MatchDate": "2026-04-16 15:00:00",
      "HomeScore": 1,
      "AwayScore": 3,
      "Status": "FT",
      "Elapsed": 90
    }
  ],
  "events": [],
  "statistics": [],
  "team_location_statistics": [
    {
      "TeamID": 41,
      "TeamName": "Southampton",
      "Venue": "home",
      "Values": {
        "last_five_form": "WLWDW",
        "wins": 8,
        "losses": 3,
        "goals_for_average": 1.4,
        "goals_against_average": 1.1,
        "failed_to_score": 2
      }
    }
  ],
  "h2h": {
    "home_vs_away": [],
    "away_vs_home": []
  }
}
```

Notes:

- This endpoint refreshes fixture events, fixture statistics, and team statistics before returning the response.
- `data` is returned as a one-item array rather than a single object.
- `h2h.home_vs_away` contains recent matches where the current home team was home.
- `h2h.away_vs_home` contains recent matches where the current away team was home.

Status codes:

- `200` on success
- `404` if the fixture is not found

## Quick cURL Examples

Get recent fixtures:

```bash
curl http://127.0.0.1:5000/api/fixtures
```

Log in and store the session cookie:

```bash
curl -c cookies.txt \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"password123"}' \
  http://127.0.0.1:5000/auth/login
```

Use the saved cookie to fetch the current user:

```bash
curl -b cookies.txt http://127.0.0.1:5000/api/me
```

Add a favourite team:

```bash
curl -b cookies.txt \
  -H "Content-Type: application/json" \
  -d '{"team_id":41}' \
  http://127.0.0.1:5000/api/me/favourite-teams
```
