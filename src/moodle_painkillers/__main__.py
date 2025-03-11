from . import main
from .discord import send_discord_notification

try:
    main()
    message: str = "Sent presence status!"
except Exception as e:
    message: str = str(e)

send_discord_notification(message)