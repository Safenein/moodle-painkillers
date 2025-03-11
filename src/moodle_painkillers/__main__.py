from . import main
import requests as rq
import json
import os

try:
    main()
    message: str = "Sent presence status!"
except Exception as e:
    message: str = str(e)

discord_webhook = os.getenv("DISCORD_WEBHOOK") or ""
if discord_webhook:
    data = {
        "content": f"{message}",
    }
    try:
        res = rq.post(
            discord_webhook,
            data=json.dumps(data),
            headers={"Content-Type": "application/json"},
        )
        print(f"Notification Discord envoyée: {res.status_code}, {res.text}")
    except Exception as e:
        print(f"Erreur d'envoi de notification Discord: {str(e)}")
