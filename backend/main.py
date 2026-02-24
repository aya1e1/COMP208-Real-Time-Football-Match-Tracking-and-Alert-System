import requests
import sqlite3

conn = sqlite3.connect("schema.sql")
cursor = conn.cursor()

API_LINK = ""
API_KEY = ""

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

def manage_table(data) {

}

if __name__ == "__main__":
    pass