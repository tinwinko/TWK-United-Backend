import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests


ESPN_URL = (
    "https://site.api.espn.com/apis/site/v2/"
    "sports/soccer/eng.1/scoreboard"
)

OUTPUT_FILE = Path("twk_data.json")

SEARCH_DAYS = 120
CHUNK_DAYS = 7


def get_scoreboard(start_date, end_date):

    params = {
        "dates": (
            f"{start_date.strftime('%Y%m%d')}-"
            f"{end_date.strftime('%Y%m%d')}"
        ),
        "limit": 100
    }

    print(
        f"Searching {params['dates']}..."
    )

    response = requests.get(
        ESPN_URL,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


def main():

    print("🔴 TWK United Data Updater")
    print("=" * 50)

    now = datetime.now(timezone.utc)

    search_start = now.date()

    search_end = (
        search_start +
        timedelta(days=SEARCH_DAYS)
    )

    all_events = []

    current_date = search_start

    while current_date < search_end:

        chunk_end = min(
            current_date +
            timedelta(days=CHUNK_DAYS - 1),
            search_end
        )

        try:

            data = get_scoreboard(
                current_date,
                chunk_end
            )

            events = data.get(
                "events",
                []
            )

            print(
                f"  → {len(events)} event(s)"
            )

            all_events.extend(events)

        except requests.HTTPError as error:

            print(
                f"⚠️ Request failed: {error}"
            )

        current_date = (
            chunk_end +
            timedelta(days=1)
        )


    print()
    print(
        f"Total events collected: "
        f"{len(all_events)}"
    )


    future_matches = []

    now_timestamp = int(
        now.timestamp()
    )


    for event in all_events:

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


        home_team = home.get(
            "team",
            {}
        )

        away_team = away.get(
            "team",
            {}
        )

        home_name = home_team.get(
            "displayName",
            ""
        )

        away_name = away_team.get(
            "displayName",
            ""
        )


        # Manchester United only
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


        if (
            int(match_time.timestamp())
            <= now_timestamp
        ):
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

        venue_name = venue.get(
            "fullName",
            ""
        )

        address = venue.get(
            "address",
            {}
        )

        venue_city = address.get(
            "city",
            ""
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
            "Premier League",

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
    print("=" * 50)

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False
        )
    )


if __name__ == "__main__":
    main()
