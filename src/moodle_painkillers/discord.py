import os
import json
import requests as rq

def send_discord_notification(message: str):
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
