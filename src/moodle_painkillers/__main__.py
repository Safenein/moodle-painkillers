from . import main, parse_args
from .discord import send_discord_notification

args = parse_args()
try:
    main(args)
    message: str = "Sent presence status!"
except Exception as e:
    message: str = str(e)

if args.discord_webhook:
    send_discord_notification(message, discord_webhook=args.discord_webhook)