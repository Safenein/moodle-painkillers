from . import main, parse_args
from .discord import send_discord_notification
from .desktop_notifications import send_notification
import logging

# Try to import rich and set up enhanced tracebacks and logging if available
try:
    from rich.traceback import install as install_rich_traceback
    from rich.logging import RichHandler
    
    # Install rich traceback for better exception visualization
    install_rich_traceback(show_locals=True)
    
    # Set up rich logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)]
    )
    logger = logging.getLogger("moodle_painkillers")
    logger.info("Rich logger and traceback installed")
except ImportError:
    # Rich is not available, use standard logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("moodle_painkillers")
    logger.info("Standard logging initialized (Rich not available)")

args = parse_args()
try:
    main(args)
    message: str = "Sent presence status!"
    logger.info(message)
except Exception as e:
    message: str = str(e)
    logger.exception("Error occurred")

if args.discord_webhook:
    send_discord_notification(message, discord_webhook=args.discord_webhook)

send_notification(message)