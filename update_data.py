import json
from datetime import datetime, timezone
from pathlib import Path

import requests

# ESPN Premier League
ESPN_URL = (
    "https://site.api.espn.com/apis/site/v2/"
    "sports/soccer/eng.1/teams/360/schedule"
)

OUTPUT_FILE = Path("twk_data.json")


def get_schedule():
    print("🔴 TWK United Data Updater")
    print("=" * 50)
    print("Fetching Manchester United schedule from ESPN...")

    response = requests.get(
        ESPN_URL,
        timeout=30,
        headers={
            "User-Agent": "TWK-United/1.0"
        }
    )

    print(f"HTTP Status: {response.status_code}")
    response.raise_for_status()

    return response.json()


def main():
    try:
        data = get_schedule()
    except Exception as error:
        print(f"❌ ESPN request failed: {error}")
        raise

    events = data.get("events", [])

    print(f"Total events received: {len(events)}")

    now_timestamp = int(datetime.now(timezone.utc).timestamp())

    future_matches = []

    for event in events:
        event_date = event.get("date")

        if not event_date:
            continue

        try:
            match_time = datetime.fromisoformat(
                event_date.replace("Z", "+00:00")
            )
        except ValueError:
            continue

        # Only future matches
        if int(match_time.timestamp()) <= now_timestamp:
            continue

        competitions = event.get("competitions", [])

        if not competitions:
            continue

        competition = competitions[0]
        competitors = competition.get("competitors", [])

        home = None
        away = None

        for competitor in competitors:
            if competitor.get("homeAway") == "home":
                home = competitor
            elif competitor.get("homeAway") == "away":
                away = competitor

        if not home or not away:
            continue

        home_team = home.get("team", {})
        away_team = away.get("team", {})

        home_name = home_team.get(
            "displayName",
            home_team.get("name", "")
        )

        away_name = away_team.get(
            "displayName",
            away_team.get("name", "")
        )

        future_matches.append({
            "event": event,
            "competition": competition,
            "home": home,
            "away": away,
            "match_time": match_time,
            "home_name": home_name,
            "away_name": away_name
        })

    future_matches.sort(
        key=lambda item: item["match_time"]
    )

    result = {
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "source": "ESPN Public Soccer API",
        "nextMatch": None
    }

    if not future_matches:
        print("⚠️ No future Manchester United match found.")

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

    item = future_matches[0]

    event = item["event"]
    competition = item["competition"]
    home = item["home"]
    away = item["away"]
    match_time = item["match_time"]

    home_team = home.get("team", {})
    away_team = away.get("team", {})

    # Venue
    venue_name = ""
    venue_city = ""

    venue = competition.get("venue")

    if venue:
        venue_name = venue.get(
            "fullName",
            venue.get("displayName", "")
        )

        address = venue.get("address", {})

        if address:
            venue_city = address.get("city", "")

    # Competition name
    competition_name = ""

    if competition.get("league"):
        competition_name = competition["league"].get(
            "name",
            ""
        )

    if not competition_name:
        competition_name = "Premier League"

    result["nextMatch"] = {
        "fixtureId": event.get("id"),

        "dateUtc": event.get("date"),

        "timestamp": int(
            match_time.timestamp()
        ),

        "status": event.get(
            "status",
            {}
        ).get(
            "type",
            {}
        ).get(
            "name"
        ),

        "competition": competition_name,

        "round": event.get(
            "season",
            {}
        ).get(
            "slug"
        ),

        "homeTeam": home_team.get(
            "displayName",
            home_team.get("name", "")
        ),

        "awayTeam": away_team.get(
            "displayName",
            away_team.get("name", "")
        ),

        "homeLogo": home_team.get("logo"),

        "awayLogo": away_team.get("logo"),

        "venue": venue_name,

        "city": venue_city
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
    print("=" * 50)

    print(
        f"🏠 Home : "
        f"{result['nextMatch']['homeTeam']}"
    )

    print(
        f"✈️ Away : "
        f"{result['nextMatch']['awayTeam']}"
    )

    print(
        f"📅 Date : "
        f"{result['nextMatch']['dateUtc']}"
    )

    print(
        f"🏟 Venue: "
        f"{result['nextMatch']['venue']}"
    )

    print()
    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False
        )
    )


if __name__ == "__main__":
    main()
