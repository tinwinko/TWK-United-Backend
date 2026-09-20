import json
import os
from pathlib import Path

import requests
import firebase_admin
from firebase_admin import credentials, messaging


API_URL = "https://v3.football.api-sports.io/fixtures"
TEAM_ID = 33
TOPIC = "manutd_live"

STATE_FILE = Path("state.json")


def load_state():
    if not STATE_FILE.exists():
        return {}

    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {}


def save_state(state):
    STATE_FILE.write_text(
        json.dumps(state, indent=2)
    )


def get_live_match():
    api_key = os.environ["API_FOOTBALL_KEY"]

    headers = {
        "x-apisports-key": api_key
    }

    params = {
        "team": TEAM_ID,
        "live": "all"
    }

    response = requests.get(
        API_URL,
        headers=headers,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    matches = data.get("response", [])

    if not matches:
        return None

    return matches[0]


def initialize_firebase():
    service_account_json = os.environ[
        "FIREBASE_SERVICE_ACCOUNT"
    ]

    service_account_info = json.loads(
        service_account_json
    )

    cred = credentials.Certificate(
        service_account_info
    )

    firebase_admin.initialize_app(cred)


def send_notification(title, body):
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body
        ),
        topic=TOPIC
    )

    response = messaging.send(message)

    print("FCM sent:", response)


def main():
    print("🔴 TWK United Goal Checker")
    print("Checking Manchester United live match...")

    match = get_live_match()

    if match is None:
        print("No Manchester United live match.")
        return

    fixture = match["fixture"]
    teams = match["teams"]
    goals = match["goals"]

    fixture_id = str(fixture["id"])

    home_name = teams["home"]["name"]
    away_name = teams["away"]["name"]

    home_goals = goals["home"] or 0
    away_goals = goals["away"] or 0

    current_score = {
        "home": home_goals,
        "away": away_goals
    }

    state = load_state()

    previous = state.get(fixture_id)

    print(
        f"{home_name} {home_goals} - "
        f"{away_goals} {away_name}"
    )

    if previous is not None:
        previous_home = previous["home"]
        previous_away = previous["away"]

        goal_changed = (
            home_goals > previous_home
            or away_goals > previous_away
        )

        if goal_changed:
            if home_goals > previous_home:
                scorer_team = home_name
            else:
                scorer_team = away_name

            title = "⚽ GOAL! 🔴 TWK UNITED"

            body = (
                f"{scorer_team} scored!\n"
                f"{home_name} {home_goals} - "
                f"{away_goals} {away_name}"
            )

            print("🚨 GOAL DETECTED!")
            send_notification(title, body)

    state[fixture_id] = current_score
    save_state(state)

    print("State saved.")


if __name__ == "__main__":
    initialize_firebase()
    main()
