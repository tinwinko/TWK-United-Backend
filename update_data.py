import json
import os
from datetime import datetime, timezone
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

    return data.get("response", [])


def main():
    print("🔴 TWK United Data Updater")
    print("Getting next Manchester United fixture...")

    fixtures = get_next_fixture()

    # Always create twk_data.json
    result = {
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "nextMatch": None
    }

    if not fixtures:
        print("⚠️ No upcoming fixture found.")
        print("Creating empty fixture data file.")

        OUTPUT_FILE.write_text(
            json.dumps(result, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

        print("✅ twk_data.json created")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    fixture = fixtures[0]

    fixture_info = fixture.get("fixture", {})
    teams = fixture.get("teams", {})
    league = fixture.get("league", {})
    venue = fixture_info.get("venue") or {}

    result["nextMatch"] = {
        "fixtureId": fixture_info.get("id"),
        "dateUtc": fixture_info.get("date"),
        "timestamp": fixture_info.get("timestamp"),

        "competition": league.get("name"),
        "round": league.get("round"),

        "homeTeam": teams.get("home", {}).get("name"),
        "awayTeam": teams.get("away", {}).get("name"),

        "homeLogo": teams.get("home", {}).get("logo"),
        "awayLogo": teams.get("away", {}).get("logo"),

        "venue": venue.get("name"),
        "city": venue.get("city")
    }

    OUTPUT_FILE.write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print("✅ twk_data.json created")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
