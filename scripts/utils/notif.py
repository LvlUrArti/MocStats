"""Send notification."""

import platform
from subprocess import run


def send_notification(title: str, message: str) -> None:
    """Send a native desktop notification depending on the operating system."""
    current_os = platform.system()

    try:
        if current_os == "Darwin":  # macOS
            apple_script = f'display notification "{message}" with title "{
                title
            }" sound name "Glass"'
            run(["osascript", "-e", apple_script], check=False)

        elif current_os == "Windows":
            # Uses built-in PowerShell to trigger a Windows balloon/toast notification
            ps_script = (
                f"[void] [System.Reflection.Assembly]::"
                "LoadWithPartialName('System.Windows.Forms'); "
                f"$objNotifyIcon = New-Object System.Windows.Forms.NotifyIcon; "
                f"$objNotifyIcon.Icon = [System.Drawing.SystemIcons]::Information; "
                f"$objNotifyIcon.BalloonTipTitle = '{title}'; "
                f"$objNotifyIcon.BalloonTipText = '{message}'; "
                f"$objNotifyIcon.Visible = $True; "
                f"$objNotifyIcon.ShowBalloonTip(10000)"
            )
            run(["powershell", "-Command", ps_script], check=False)

        elif current_os == "Linux":
            # Works on Ubuntu, Fedora, Debian, Mint etc.
            run(["notify-send", title, message], check=False)

    except Exception as e:
        print(f"⚠️ Failed to send desktop notification: {e}")
