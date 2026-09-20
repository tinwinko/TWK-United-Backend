import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests


ESPN_URL = (
    "https://site.api.espn.com/apis/site/v2/"
    "sports/soccer/eng.1/scoreboard"
)

OUTPUT_FILE = Path("twk_data.json")


def get_scoreboard():

    today = datetime.now(timezone.utc).date()

    end_date = today + timedelta(days=120)

    params = {
        "dates": (
            f"{today.strftime('%Y%m%d')}-"
            f"{end_date.strftime('%Y%m%d')}"
        ),
        "limit": 200
    }

    print("🔴 TWK United Data Updater")
    print("=" * 45)

    print(
        f"Searching: "
        f"{params['dates']}"
    )

    response = requests.get(
        ESPN_URL,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


def main():

    data = get_scoreboard()

    events = data.get(
        "events",
        []
    )

    print(
        f"API returned {len(events)} events"
    )

    now = datetime.now(timezone.utc)

    future_matches = []

    for event in events:

        competitions = event.get(
            "competitions",
            []
        )

        if not competitions:
            continue

        competition = competitions[0]

        competitors = competition.get(
            "competitors",
            []
        )

        home = None
        away = None

        for team in competitors:

            if team.get("homeAway") == "home":
                home = team

            elif team.get("homeAway") == "away":
                away = team

        if not home or not away:
            continue

        home_name = (
            home.get("team", {})
            .get("displayName", "")
        )

        away_name = (
            away.get("team", {})
            .get("displayName", "")
        )

        # Only Manchester United matches
        if (
            "Manchester United" not in home_name
            and
            "Manchester United" not in away_name
        ):
            continue

        event_date = event.get(
            "date"
        )

        if not event_date:
            continue

        try:

            match_time = datetime.fromisoformat(
                event_date.replace(
                    "Z",
                    "+00:00"
                )
            )

        except ValueError:

            continue

        if match_time <= now:
            continue

        future_matches.append(
            {
                "event": event,
                "competition": competition,
                "home": home,
                "away": away,
                "match_time": match_time
            }
        )


    # Sort nearest first
    future_matches.sort(
        key=lambda item:
        item["match_time"]
    )


    result = {
        "updatedAt":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "source":
            "ESPN Public Soccer API",

        "nextMatch":
            None
    }


    if not future_matches:

        print()
        print(
            "❌ No upcoming Manchester United match found."
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


    item = future_matches[0]

    event = item["event"]
    competition = item["competition"]
    home = item["home"]
    away = item["away"]
    match_time = item["match_time"]


    home_team = home.get(
        "team",
        {}
    )

    away_team = away.get(
        "team",
        {}
    )


    # Venue
    venue_name = ""

    venue_city = ""

    venue = competition.get(
        "venue"
    )

    if venue:

        venue_info = venue.get(
            "fullName",
            ""
        )

        venue_name = venue_info

        address = venue.get(
            "address",
            {}
        )

        venue_city = address.get(
            "city",
            ""
        )


    # Competition name
    league_name = (
        competition
        .get("type", {})
        .get(
            "text",
            "Premier League"
        )
    )


    result["nextMatch"] = {

        "fixtureId":
            event.get("id"),

        "dateUtc":
            event.get("date"),

        "timestamp":
            int(
                match_time.timestamp()
            ),

        "status":
            event
            .get("status", {})
            .get("type", {})
            .get("name"),

        "competition":
            league_name,

        "round":
            event
            .get("season", {})
            .get("slug"),

        "homeTeam":
            home_team.get(
                "displayName"
            ),

        "awayTeam":
            away_team.get(
                "displayName"
            ),

        "homeLogo":
            home_team.get(
                "logo"
            ),

        "awayLogo":
            away_team.get(
                "logo"
            ),

        "venue":
            venue_name,

        "city":
            venue_city
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
