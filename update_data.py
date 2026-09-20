import json
from datetime import datetime, timezone
from pathlib import Path

import requests


OUTPUT_FILE = Path("twk_data.json")

BASE_URL = "https://footballapi.pulselive.com/football"

HEADERS = {
    "Origin": "https://www.premierleague.com",
    "Referer": "https://www.premierleague.com/",
    "account": "premierleague",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Accept": "application/json",
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/153.0.0.0 Safari/537.36"
    ),
}


# ============================================================
# 2026/27 PREMIER LEAGUE SEASON
# ============================================================

def get_current_season():
    # 2026/27 Premier League PulseLive season ID
    season_id = 841

    print("🔴 Using Premier League 2026/27 season...")
    print("=" * 50)
    print("✅ Season: 2026/27")
    print(f"✅ Season ID: {season_id}")

    return season_id


# ============================================================
# GET FIXTURES
# ============================================================

def get_fixtures(season_id):
    print()
    print("Fetching Premier League fixtures...")
    print("=" * 50)

    url = f"{BASE_URL}/fixtures"

    all_fixtures = []

    page = 0
    page_size = 40

    while True:

        params = {
            "comps": 1,
            "compSeasons": season_id,
            "page": page,
            "pageSize": page_size,
            "sort": "asc",
            "altIds": "true",
        }

        print(
            f"Requesting fixtures page "
            f"{page + 1}..."
        )

        response = requests.get(
            url,
            params=params,
            headers=HEADERS,
            timeout=30,
        )

        print(
            f"  HTTP Status: "
            f"{response.status_code}"
        )

        if response.status_code != 200:
            print(
                "❌ Fixture request failed."
            )

            print(
                "Response:"
            )

            print(
                response.text[:2000]
            )

        response.raise_for_status()

        data = response.json()

        content = data.get(
            "content",
            []
        )

        print(
            f"  → {len(content)} fixture(s)"
        )

        if not content:
            break

        all_fixtures.extend(
            content
        )

        page_info = data.get(
            "pageInfo",
            {}
        )

        num_pages = page_info.get(
            "numPages"
        )

        if num_pages is not None:

            try:

                if (
                    page + 1
                    >= int(num_pages)
                ):
                    break

            except Exception:
                pass

        if len(content) < page_size:
            break

        page += 1

        # Safety limit
        if page >= 20:
            print(
                "⚠️ Safety page limit reached."
            )
            break

    print()

    print(
        f"Total fixtures received: "
        f"{len(all_fixtures)}"
    )

    return all_fixtures


# ============================================================
# TEAM NAME
# ============================================================

def get_team_name(team):

    if not team:
        return ""

    return (
        team.get("name")
        or team.get("shortName")
        or team.get("club", {}).get("name")
        or ""
    )


# ============================================================
# KICKOFF TIME
# ============================================================

def parse_kickoff(fixture):

    kickoff = fixture.get(
        "kickoff"
    )

    if not kickoff:
        return None

    # Primary method
    millis = kickoff.get(
        "millis"
    )

    if millis:

        try:

            return datetime.fromtimestamp(
                int(millis) / 1000,
                tz=timezone.utc,
            )

        except Exception:
            pass

    # Fallback method
    iso = kickoff.get(
        "iso"
    )

    if iso:

        try:

            return datetime.fromisoformat(
                iso.replace(
                    "Z",
                    "+00:00"
                )
            )

        except Exception:
            pass

    return None


# ============================================================
# FIND NEXT MANCHESTER UNITED MATCH
# ============================================================

def find_next_manchester_united_fixture(
    fixtures
):

    now = datetime.now(
        timezone.utc
    )

    future_matches = []

    for fixture in fixtures:

        teams = fixture.get(
            "teams",
            []
        )

        if len(teams) < 2:
            continue

        home = None
        away = None

        for team_entry in teams:

            team = team_entry.get(
                "team",
                {}
            )

            team_name = get_team_name(
                team
            )

            if (
                "Manchester United"
                not in team_name
            ):
                continue

            if team_entry.get(
                "home"
            ):
                home = team_entry

            else:
                away = team_entry

        if not home and not away:
            continue

        kickoff = parse_kickoff(
            fixture
        )

        if not kickoff:
            continue

        # Ignore matches that already started/finished
        if kickoff <= now:
            continue

        if not home or not away:
            continue

        future_matches.append(
            {
                "fixture": fixture,
                "home": home,
                "away": away,
                "kickoff": kickoff,
            }
        )

    future_matches.sort(
        key=lambda item:
        item["kickoff"]
    )

    if not future_matches:
        return None

    return future_matches[0]


# ============================================================
# BUILD NEXT MATCH JSON
# ============================================================

def build_result(item):

    fixture = item[
        "fixture"
    ]

    home = item[
        "home"
    ]

    away = item[
        "away"
    ]

    kickoff = item[
        "kickoff"
    ]

    home_team = home.get(
        "team",
        {}
    )

    away_team = away.get(
        "team",
        {}
    )

    competition = fixture.get(
        "competition",
        {}
    )

    ground = fixture.get(
        "ground",
        {}
    )

    home_name = get_team_name(
        home_team
    )

    away_name = get_team_name(
        away_team
    )

    # Try multiple possible venue fields
    venue_name = (
        ground.get("name")
        or ground.get("shortName")
        or ""
    )

    venue_city = (
        ground.get("city")
        or ""
    )

    return {

        "fixtureId": fixture.get(
            "id"
        ),

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

        "round": fixture.get(
            "gameweek"
        ),

        "homeTeam": home_name,

        "awayTeam": away_name,

        "homeLogo": (
            home_team
            .get("club", {})
            .get("shortName")
        ),

        "awayLogo": (
            away_team
            .get("club", {})
            .get("shortName")
        ),

        "venue": venue_name,

        "city": venue_city,
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "🔴 TWK United Data Updater"
    )

    print("=" * 50)

    # --------------------------------------------------------
    # 1. Get season
    # --------------------------------------------------------

    season_id = (
        get_current_season()
    )

    # --------------------------------------------------------
    # 2. Get fixtures
    # --------------------------------------------------------

    fixtures = get_fixtures(
        season_id
    )

    # --------------------------------------------------------
    # 3. Find next Manchester United match
    # --------------------------------------------------------

    next_match = (
        find_next_manchester_united_fixture(
            fixtures
        )
    )

    # --------------------------------------------------------
    # 4. Base JSON
    # --------------------------------------------------------

    result = {

        "updatedAt":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "source":
            "Premier League PulseLive Public Data",

        "nextMatch":
            None,
    }

    # --------------------------------------------------------
    # 5. No match
    # --------------------------------------------------------

    if not next_match:

        print()

        print(
            "⚠️ No upcoming "
            "Manchester United "
            "fixture found."
        )

    # --------------------------------------------------------
    # 6. Match found
    # --------------------------------------------------------

    else:

        result[
            "nextMatch"
        ] = build_result(
            next_match
        )

        match = result[
            "nextMatch"
        ]

        print()

        print(
            "✅ NEXT MATCH FOUND"
        )

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
            f"📅 UTC : "
            f"{match['dateUtc']}"
        )

        print(
            f"🏟 Venue: "
            f"{match['venue']}"
        )

        print(
            f"🏙 City : "
            f"{match['city']}"
        )

        print(
            f"🆔 ID : "
            f"{match['fixtureId']}"
        )

        print(
            f"⏱ Timestamp : "
            f"{match['timestamp']}"
        )

    # --------------------------------------------------------
    # 7. Save JSON
    # --------------------------------------------------------

    OUTPUT_FILE.write_text(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print()

    print(
        "✅ twk_data.json created"
    )

    print()

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
        )
    )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()
