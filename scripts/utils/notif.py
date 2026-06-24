"""Send notification."""
# pyright: reportMissingTypeStubs=false, reportOptionalCall=false

from time import sleep

from plyer import notification


def send_notification(title: str, message: str) -> None:
    """Send a notification."""
    notification.notify(title, message, timeout=2)
    sleep(0.1)
