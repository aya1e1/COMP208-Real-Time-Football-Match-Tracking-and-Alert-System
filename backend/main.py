import requests
import sqlite3
from pathlib import Path

from dummy import mock_responses

import responses

current_file = Path(__file__).resolve()
schema_path = current_file.parent.parent / "database" / "schema.sql"
db_path = current_file.parent.parent / "database" / "database.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

#API_LINK = "https://v3.football.api-sports.io/"
API_KEY = "7f14422097825f6406284820ff8f58cc"
API_LINK = "http://example.com"

mock_responses.register_mocks()
@responses.activate
def get(request):
    headers = {
        "x-apisports-key": API_KEY,
    }
    try:
        response = requests.request("GET", API_LINK + request, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        print(e)


def process_league(data):
     
    ## add sql command to check if the league exists, if not then add into League table and seasons
    for data in data["response"]:
        leagueid = data["league"]["id"]
        seasons = data["seasons"]
        if data["country"]["name"] == "England" and leagueid < 42:
            for season in seasons:
                Name = data["league"]["name"]
                SeasonID = season["year"]
                StartDate = season["start"]
                EndDate = season["end"]
                print(leagueid)
                print(Name)
                print(SeasonID)
                print(StartDate)
                print(EndDate)


def init_db():
    try:
        with open(schema_path, 'r') as f: # reads schema
            sql_script = f.read()
        # ensure foreign keys are enforced in SQLite
        cursor.execute('PRAGMA foreign_keys = ON;')
        
        cursor.executescript(sql_script)
        conn.commit() # saves
        print("Database initialised")
    except Exception as e:
        print(e)
    finally:
        conn.close()


if __name__ == "__main__":
    try: # check if db has been initialised
        query = "SELECT * FROM Player" 
        cursor.execute(query) 
        print(cursor.fetchall())
    except Exception as e: # if not, initialise db
        print(e)
        init_db()

    print("data:")
    league_data = get("/leagues")
    process_league(league_data)
    
    
