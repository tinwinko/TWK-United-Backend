import json
import os

import firebase_admin
from firebase_admin import credentials, messaging


def main():
    service_account_json = os.environ["FIREBASE_SERVICE_ACCOUNT"]

    service_account_info = json.loads(
        service_account_json
    )

    credential = credentials.Certificate(
        service_account_info
    )

    firebase_admin.initialize_app(credential)

    message = messaging.Message(
        notification=messaging.Notification(
            title="🔴 TWK UNITED",
            body="⚽ Backend Test — GitHub Actions → FCM is working!"
        ),
        topic="manutd_live"
    )

    response = messaging.send(message)

    print("✅ FCM notification sent successfully")
    print("Message ID:", response)


if __name__ == "__main__":
    main()
