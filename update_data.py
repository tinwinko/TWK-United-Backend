import json
from datetime import datetime, timezone
from pathlib import Path

import requests


OUTPUT_FILE = Path("twk_data.json")

BASE_URL = "https://footballapi.pulselive.com/football"

HEADERS = {
    "Origin": "https://www.premierleague.com",
    "Referer": "https://www.premierleague.com/",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/153.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}


def get_current_season():
    print("🔴 Getting current Premier League season...")

    url = f"{BASE_URL}/competitions/1/compseasons"

    response = requests.get(
        url,
        headers=HEADERS,
        params={
            "pageSize": 20,
            "page": 0,
        },
        timeout=30,
    )

    print(f"Season API HTTP Status: {response.status_code}")

    response.raise_for_status()

    data = response.json()

    seasons = data.get("content", [])

    if not seasons:
        raise RuntimeError("No Premier League seasons returned.")

    # Find 2026/27 first
    for season in seasons:
        label = str(season.get("label", ""))

        if "2026/27" in label:
            print(
                f"✅ Current season found: "
                f"{label} (ID {season.get('id')})"
            )
            return season["id"]

    # Fallback to first season
    season = seasons[0]

    print(
        f"⚠️ 2026/27 not found. "
        f"Using {season.get('label')} "
        f"(ID {season.get('id')})"
    )

    return season["id"]


def get_fixtures(season_id):
    print()
    print("Fetching Premier League fixtures...")

    url = f"{BASE_URL}/fixtures"

    response = requests.get(
        url,
        headers=HEADERS,
        params={
            "comps": 1,
            "compSeasons": season_id,
            "page": 0,
            "pageSize": 500,
            "sort": "asc",
            "altIds": "true",
        },
        timeout=30,
    )

    print(f"Fixtures API HTTP Status: {response.status_code}")

    response.raise_for_status()

    data = response.json()

    fixtures = data.get("content", [])

    print(f"Total fixtures received: {len(fixtures)}")

    return fixtures


def parse_kickoff(fixture):
    kickoff = fixture.get("kickoff")

    if not kickoff:
        return None

    millis = kickoff.get("millis")

    if millis:
        try:
            return datetime.fromtimestamp(
                int(millis) / 1000,
                tz=timezone.utc,
            )
        except Exception:
            pass

    iso = kickoff.get("iso")

    if iso:
        try:
            return datetime.fromisoformat(
                iso.replace("Z", "+00:00")
            )
        except Exception:
            pass

    return None


def find_next_manchester_united_fixture(fixtures):
    now = datetime.now(timezone.utc)

    future = []

    for fixture in fixtures:
        teams = fixture.get("teams", [])

        if len(teams) < 2:
            continue

        home = None
        away = None

        for team in teams:
            if team.get("team", {}).get("name") == "Manchester United":
                if team.get("home"):
                    home = team
                else:
                    away = team

        if not home and not away:
            continue

        kickoff = parse_kickoff(fixture)

        if not kickoff:
            continue

        if kickoff <= now:
            continue

        if not home or not away:
            continue

        future.append(
            {
                "fixture": fixture,
                "home": home,
                "away": away,
                "kickoff": kickoff,
            }
        )

    future.sort(
        key=lambda item: item["kickoff"]
    )

    return future[0] if future else None


def build_result(item):
    fixture = item["fixture"]
    home = item["home"]
    away = item["away"]
    kickoff = item["kickoff"]

    home_team = home.get("team", {})
    away_team = away.get("team", {})

    venue = fixture.get("ground", {})

    competition = fixture.get(
        "competition",
        {}
    )

    return {
        "fixtureId": fixture.get("id"),

        "dateUtc": kickoff.isoformat(),

        "timestamp": int(
            kickoff.timestamp()
        ),

        "status": fixture.get(
            "status",
            "U"
        ),

        "competition": competition.get(
            "name",
            "Premier League"
        ),

        "round": (
            fixture.get("gameweek", {})
            .get("gameweek")
        ),

        "homeTeam": home_team.get(
            "name"
        ),

        "awayTeam": away_team.get(
            "name"
        ),

        "homeLogo": home_team.get(
            "club",
            {}
        ).get(
            "shortName"
        ),

        "awayLogo": away_team.get(
            "club",
            {}
        ).get(
            "shortName"
        ),

        "venue": venue.get(
            "name",
            ""
        ),

        "city": venue.get(
            "city",
            ""
        ),
    }


def main():
    print("🔴 TWK United Data Updater")
    print("=" * 50)

    season_id = get_current_season()

    fixtures = get_fixtures(
        season_id
    )

    next_match = (
        find_next_manchester_united_fixture(
            fixtures
        )
    )

    result = {
        "updatedAt": datetime.now(
            timezone.utc
        ).isoformat(),

        "source": (
            "Premier League "
            "Official Public Data"
        ),

        "nextMatch": None,
    }

    if not next_match:
        print()
        print(
            "⚠️ No upcoming "
            "Manchester United fixture found."
        )

    else:
        result["nextMatch"] = build_result(
            next_match
        )

        match = result["nextMatch"]

        print()
        print("✅ NEXT MATCH FOUND")
        print("=" * 50)

        print(
            f"🏠 Home : "
            f"{match['homeTeam']}"
        )

        print(
            f"✈️ Away : "
            f"{match['awayTeam']}"
        )

        print(
            f"📅 Date : "
            f"{match['dateUtc']}"
        )

        print(
            f"🏟 Venue: "
            f"{match['venue']}"
        )

    OUTPUT_FILE.write_text(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print()
    print("✅ twk_data.json created")
    print()

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
