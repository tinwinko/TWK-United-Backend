import json
import os
from datetime import datetime, timezone
from pathlib import Path

import requests

API_URL = "https://v3.football.api-sports.io/fixtures"

TEAM_ID = 33
PREMIER_LEAGUE_ID = 39
CURRENT_SEASON = 2026

OUTPUT_FILE = Path("twk_data.json")


def api_request(params):
    api_key = os.environ["API_FOOTBALL_KEY"]

    response = requests.get(
        API_URL,
        headers={
            "x-apisports-key": api_key
        },
        params=params,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    if data.get("errors"):
        print("⚠️ API errors:")
        print(json.dumps(data["errors"], indent=2))

    return data


def get_next_fixture():

    # First: direct team + next request
    print("1️⃣ Trying team=33&next=10...")

    data = api_request({
        "team": TEAM_ID,
        "next": 10
    })

    fixtures = data.get("response", [])

    print(
        f"API returned {len(fixtures)} fixture(s)"
    )

    if fixtures:
        return fixtures


    # Second: Premier League 2026 season
    print(
        "2️⃣ Trying Premier League 2026 "
        "with team=33..."
    )

    data = api_request({
        "league": PREMIER_LEAGUE_ID,
        "season": CURRENT_SEASON,
        "team": TEAM_ID
    })

    fixtures = data.get("response", [])

    print(
        f"API returned {len(fixtures)} fixture(s)"
    )

    return fixtures


def main():

    print("🔴 TWK United Data Updater")
    print("=" * 40)

    fixtures = get_next_fixture()

    result = {
        "updatedAt": datetime.now(
            timezone.utc
        ).isoformat(),
        "nextMatch": None
    }

    if not fixtures:

        print()
        print(
            "❌ No fixture returned by API."
        )

        OUTPUT_FILE.write_text(
            json.dumps(
                result,
                indent=2,
                ensure_ascii=False
            ),
            encoding="utf-8"
        )

        print(
            "✅ twk_data.json created"
        )

        return


    # Find the first future fixture
    now_timestamp = int(
        datetime.now(timezone.utc).timestamp()
    )

    future_fixture = None

    for fixture in fixtures:

        fixture_info = fixture.get(
            "fixture",
            {}
        )

        timestamp = fixture_info.get(
            "timestamp"
        )

        if timestamp and timestamp > now_timestamp:

            future_fixture = fixture
            break


    # If API already returned next fixture
    if future_fixture is None:
        future_fixture = fixtures[0]


    fixture_info = future_fixture.get(
        "fixture",
        {}
    )

    teams = future_fixture.get(
        "teams",
        {}
    )

    league = future_fixture.get(
        "league",
        {}
    )

    venue = fixture_info.get(
        "venue"
    ) or {}


    result["nextMatch"] = {

        "fixtureId":
            fixture_info.get("id"),

        "dateUtc":
            fixture_info.get("date"),

        "timestamp":
            fixture_info.get("timestamp"),

        "competition":
            league.get("name"),

        "round":
            league.get("round"),

        "homeTeam":
            teams.get("home", {}).get(
                "name"
            ),

        "awayTeam":
            teams.get("away", {}).get(
                "name"
            ),

        "homeLogo":
            teams.get("home", {}).get(
                "logo"
            ),

        "awayLogo":
            teams.get("away", {}).get(
                "logo"
            ),

        "venue":
            venue.get("name"),

        "city":
            venue.get("city")
    }


    OUTPUT_FILE.write_text(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )


    print()
    print("✅ twk_data.json created")
    print("=" * 40)

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False
        )
    )


if __name__ == "__main__":
    main()
