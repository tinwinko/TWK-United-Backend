import json
import os
from pathlib import Path

import requests

API_URL = "https://v3.football.api-sports.io/fixtures"
TEAM_ID = 33

OUTPUT_FILE = Path("twk_data.json")


def get_next_fixture():
    api_key = os.environ["API_FOOTBALL_KEY"]

    response = requests.get(
        API_URL,
        headers={
            "x-apisports-key": api_key
        },
        params={
            "team": TEAM_ID,
            "next": 1
        },
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    matches = data.get("response", [])

    if not matches:
        return None

    return matches[0]


def main():
    print("🔴 TWK United Data Updater")
    print("Getting next Manchester United fixture...")

    fixture = get_next_fixture()

    if fixture is None:
        print("No upcoming fixture found.")
        return

    fixture_info = fixture["fixture"]
    teams = fixture["teams"]
    league = fixture["league"]

    result = {
        "updatedAt": fixture_info.get("date"),
        "nextMatch": {
            "fixtureId": fixture_info.get("id"),
            "dateUtc": fixture_info.get("date"),
            "timestamp": fixture_info.get("timestamp"),
            "competition": league.get("name"),
            "round": league.get("round"),
            "homeTeam": teams["home"].get("name"),
            "awayTeam": teams["away"].get("name"),
            "homeLogo": teams["home"].get("logo"),
            "awayLogo": teams["away"].get("logo"),
            "venue": fixture_info.get("venue", {}).get("name"),
            "city": fixture_info.get("venue", {}).get("city")
        }
    }

    OUTPUT_FILE.write_text(
        json.dumps(result, indent=2, ensure_ascii=False)
    )

    print("✅ twk_data.json created")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
