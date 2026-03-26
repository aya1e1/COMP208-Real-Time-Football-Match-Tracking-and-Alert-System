"""cache.py - DB-backed cache to minimise API-Football calls (100/day limit)."""
import json
from datetime import datetime, timedelta
from backend.db.database import query,execute

class Cache:
    # Time to live constants (in seconds)
    TTL_LIVE   = 30    # Live match data - refresh every 30 sec
    TTL_TODAY  = 300   # Today's fixtures - refresh every 5 minutes
    TTL_STATIC = 86400 # Static data (teams, players) - refresh every 24 hours
    TTL_SEASON = 3600  # Season data (standings) - refresh every 1 hour

    def get(self, key):
        """Retrieve cached data by key. Returns None if the key does not exist or has expired."""
        # Look up the cache entry in the database
        rows = query("SELECT Data, ExpiresAt FROM Cache WHERE CacheKey = ?", (key,))
        # return None if no entry found
        if not rows:
            return None
        row = rows[0]
      
        # Check if cached data has expired
        if datetime.utcnow() > datetime.fromisoformat(row["ExpiresAt"]):
            # Delete the expired entry and return None to trigger a fresh API call
            execute("DELETE FROM Cache WHERE CacheKey = ?", (key,))
            return None
        # Return the cached data as a Python object
        return json.loads(row["Data"])

    def set(self, key, data, ttl=86400):
        """Store data in the cache with a time to live (TTL) in seconds.
           If the key already exists, the existing entry is updated.
        """
        now = datetime.utcnow()
        expires = now + timedelta(seconds=ttl) # calculate expiry time

        # Insert new cache entry or update existing one if key already exists
        execute(
            """INSERT INTO Cache (CacheKey, Data, FetchedAt, ExpiresAt)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(CacheKey) DO UPDATE SET
               Data=excluded.Data, FetchedAt=excluded.FetchedAt,
               ExpiresAt=excluded.ExpiresAt""",
            (key, json.dumps(data), now.isoformat(), expires.isoformat()),
        )
    def delete(self, key):
        """Remove a single cache entry by key.
        Used to force a fresh API call for a specific resource,
        for example when a live match finishes.
        """
       execute("DELETE FROM Cache WHERE CacheKey = ?", (key,))

    def purge_expired(self):
        """Remove all cache entries that have passed their expiry time.
        Should be called periodically to keep the database clean
        and prevent it from filling up with stale data.
        """
       execute("DELETE FROM Cache WHERE ExpiresAt < ?", (datetime.utcnow().isoformat(),))
