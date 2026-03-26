"""football_api.py - Wrapper for API-Football v3 with caching."""

import os
import requests
from backend.api.cache import Cache

# Base URL for API-Football v3
API_BASE = "https://v3.football.api-sports.io"

# API key loaded from .env file
API_KEY  = os.getenv("API_FOOTBALL_KEY", "")

# Shared cache instance used by all functions
cache = Cache()

def _get(endpoint, params=None):
    """Send a GET request to API-Football and return the JSON response.
    This is a private helper function - not called directly from outside.
    """
    # Set required headers for API-Football authentication
    headers = {
        "x-apisports-key": API_KEY,
        "x-rapidapi-host": "v3.football.api-sports.io",
    }
    response = requests.get(f"{API_BASE}/{endpoint}",
                            headers=headers, params=params, timeout=10)
    response.raise_for_status()  # Raise error if request failed
    return response.json()

def get_leagues(country="England"):
    """Fetch all leagues for a given country.
    Cached for 24 hours as league data rarely changes.
    """
    key = f"leagues_{country}"

    # Return cached data if available
    hit = cache.get(key)
    if hit:
        return hit

    # Fetch from API and store in cache
    data   = _get("leagues", {"country": country})
    result = data.get("response", [])
    cache.set(key, result, Cache.TTL_STATIC)
    return result

def get_standings(league_id, season):
    """Fetch league standings for a specific league and season.
    Cached for 1 hour as standings can change frequently during the season.
    """
    key = f"standings_{league_id}_{season}"
    hit = cache.get(key)
    if hit:
        return hit
    data   = _get("standings", {"league": league_id, "season": season})
    result = data.get("response", [])
    cache.set(key, result, Cache.TTL_SEASON)
    return result

def get_fixtures_by_date(date, league_id=None, season=None):
    """Fetch fixtures for a specific date.
    Cached for 5 minutes to stay up to date without overusing the API.
    """
    key = f"fixtures_{date}_{league_id}"
    hit = cache.get(key)
    if hit:
        return hit
    params = {"date": date}
    if league_id:
        params["league"] = league_id
        params["season"] = season
    data   = _get("fixtures", params)
    result = data.get("response", [])
    cache.set(key, result, Cache.TTL_TODAY)
    return result

def get_live_fixtures(league_id=None):
    """Fetch all currently live matches.
    Cached for only 30 seconds as scores change frequently.
    """
    key = f"live_{league_id or 'all'}"
    hit = cache.get(key)
    if hit:
        return hit
    params = {"live": "all"}
    if league_id:
        params["live"] = str(league_id)
    data   = _get("fixtures", params)
    result = data.get("response", [])
    cache.set(key, result, Cache.TTL_LIVE)
    return result

def get_fixture(fixture_id):
    """Fetch details for a single match by fixture ID.
    TTL depends on match status: 30 seconds if live, 5 minutes otherwise.
    """
    key = f"fixture_{fixture_id}"
    hit = cache.get(key)
    if hit:
        return hit
    data   = _get("fixtures", {"id": fixture_id})
    result = data.get("response", [{}])[0]

    # Use shorter TTL if match is currently live
    status = result.get("fixture", {}).get("status", {}).get("short", "NS")
    ttl    = Cache.TTL_LIVE if status in ("1H", "HT", "2H", "ET", "P") \
             else Cache.TTL_TODAY
    cache.set(key, result, ttl)
    return result

def get_events(fixture_id):
    """Fetch all events (goals, cards, substitutions) for a specific match.
    Cached for 30 seconds as events can happen frequently during a match.
    """
    key = f"events_{fixture_id}"
    hit = cache.get(key)
    if hit:
        return hit
    data   = _get("fixtures/events", {"fixture": fixture_id})
    result = data.get("response", [])
    cache.set(key, result, Cache.TTL_LIVE)
    return result

def get_teams(league_id, season):
    """Fetch all teams in a league for a given season.
    Cached for 24 hours as team data rarely changes.
    """
    key = f"teams_{league_id}_{season}"
    hit = cache.get(key)
    if hit:
        return hit
    data   = _get("teams", {"league": league_id, "season": season})
    result = data.get("response", [])
    cache.set(key, result, Cache.TTL_STATIC)
    return result

def get_player_stats(player_id, season):
    """Fetch statistics for a player in a given season.
    Cached for 1 hour as stats update after each match.
    """
    key = f"player_stats_{player_id}_{season}"
    hit = cache.get(key)
    if hit:
        return hit
    data   = _get("players", {"id": player_id, "season": season})
    result = data.get("response", [{}])
    cache.set(key, result, Cache.TTL_SEASON)
    return result
