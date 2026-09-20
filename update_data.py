import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests


API_URL = "https://v3.football.api-sports.io/fixtures"
TEAM_ID = 33

OUTPUT_FILE = Path("twk_data.json")


def get_fixtures():

    api_key = os.environ["API_FOOTBALL_KEY"]

    now = datetime.now(timezone.utc)

    from_date = now.date()
    to_date = (now + timedelta(days=120)).date()

    print(f"Searching fixtures from {from_date} to {to_date}...")

    response = requests.get(
        API_URL,
        headers={
            "x-apisports-key": api_key
        },
        params={
            "team": TEAM_ID,
            "from": str(from_date),
            "to": str(to_date)
        },
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    if data.get("errors"):
        print("⚠️ API errors:")
        print(
            json.dumps(
                data["errors"],
                indent=2,
                ensure_ascii=False
            )
        )

    print(
        f"API returned {data.get('results', 0)} fixture(s)"
    )

    return data.get("response", [])


def main():

    print("🔴 TWK United Data Updater")
    print("=" * 45)

    fixtures = get_fixtures()

    result = {
        "updatedAt": datetime.now(
            timezone.utc
        ).isoformat(),
        "nextMatch": None
    }

    now_timestamp = int(
        datetime.now(timezone.utc).timestamp()
    )

    future_fixtures = []

    for fixture in fixtures:

        fixture_info = fixture.get(
            "fixture",
            {}
        )

        timestamp = fixture_info.get(
            "timestamp"
        )

        status = (
            fixture_info
            .get("status", {})
            .get("short", "")
        )

        if (
            timestamp
            and timestamp > now_timestamp
            and status not in ["CANC", "PST"]
        ):
            future_fixtures.append(fixture)


    if not future_fixtures:

        print()
        print("❌ No upcoming fixture found.")

        OUTPUT_FILE.write_text(
            json.dumps(
                result,
                indent=2,
                ensure_ascii=False
            ),
            encoding="utf-8"
        )

        print("✅ twk_data.json created")

        return


    # Sort by kickoff time
    future_fixtures.sort(
        key=lambda fixture:
            fixture["fixture"]["timestamp"]
    )

    fixture = future_fixtures[0]

    fixture_info = fixture.get(
        "fixture",
        {}
    )

    teams = fixture.get(
        "teams",
        {}
    )

    league = fixture.get(
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

        "status":
            fixture_info
            .get("status", {})
            .get("short"),

        "competition":
            league.get("name"),

        "round":
            league.get("round"),

        "homeTeam":
            teams
            .get("home", {})
            .get("name"),

        "awayTeam":
            teams
            .get("away", {})
            .get("name"),

        "homeLogo":
            teams
            .get("home", {})
            .get("logo"),

        "awayLogo":
            teams
            .get("away", {})
            .get("logo"),

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
    print("✅ NEXT MATCH FOUND")
    print("=" * 45)

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False
        )
    )


if __name__ == "__main__":
    main()
