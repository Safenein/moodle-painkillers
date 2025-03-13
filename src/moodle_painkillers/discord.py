import os
import json
import requests as rq
import logging

# Set up logger for this module
log = logging.getLogger(__name__)


def send_discord_notification(message: str, *, discord_webhook: str) -> None:
    data = {
        "content": f"{message}",
    }
    try:
        res = rq.post(
            discord_webhook,
            data=json.dumps(data),
            headers={"Content-Type": "application/json"},
        )
        log.info(
            f"Notification Discord envoyée: {res.status_code}, {res.text}"
        )
    except Exception as e:
        log.error(f"Erreur d'envoi de notification Discord: {str(e)}")
