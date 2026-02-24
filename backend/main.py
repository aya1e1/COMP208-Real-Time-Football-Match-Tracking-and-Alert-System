import requests
import sqlite3

conn = sqlite3.connect("schema.sql")
cursor = conn.cursor()

API_LINK = "https://v3.football.api-sports.io/"
API_KEY = "7f14422097825f6406284820ff8f58cc"

def get(request) {
    headers = {
        "x-apisports-key": API_KEY,
    }

    try {
        response = requests.request("GET", API_LINK, headers=headers)
        response.raise_for_status()
        data = response.json()
        print(data)
    }
}

def process_data(data) {

}

if __name__ == "__main__":
    pass