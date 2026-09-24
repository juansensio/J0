"""Control J0 with the arrow keys from a terminal on the same Wi-Fi network."""

import argparse
import curses
import os
import urllib.error
import urllib.request


ARROW_COMMANDS = {
    curses.KEY_UP: "forward",
    curses.KEY_DOWN: "backward",
    curses.KEY_LEFT: "left",
    curses.KEY_RIGHT: "right",
}


def send_command(host, token, command):
    request = urllib.request.Request(
        f"http://{host}/{command}", headers={"X-Robot-Token": token}
    )
    with urllib.request.urlopen(request, timeout=2) as response:
        return response.read().decode("utf-8", errors="replace")


def control(screen, host, token):
    screen.keypad(True)
    curses.curs_set(0)
    status = "Ready"
    try:
        while True:
            screen.erase()
            screen.addstr(0, 0, "Arrows: move | Space: stop | Q: quit")
            screen.addstr(2, 0, "Each arrow starts a one-second move.")
            screen.addstr(4, 0, status[: max(0, screen.getmaxyx()[1] - 1)])
            screen.refresh()
            key = screen.getch()
            if key in (ord("q"), ord("Q")):
                break
            command = "stop" if key == ord(" ") else ARROW_COMMANDS.get(key)
            if command is None:
                continue
            try:
                status = send_command(host, token, command)
            except (OSError, urllib.error.URLError, ValueError) as exc:
                status = f"Connection error: {exc}"
    finally:
        try:
            send_command(host, token, "stop")
        except (OSError, urllib.error.URLError, ValueError):
            pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=os.getenv("ROBOT_HOST"), help="robot IP address")
    parser.add_argument("--token", default=os.getenv("ROBOT_TOKEN"), help="control token")
    args = parser.parse_args()
    if not args.host or not args.token:
        parser.error("set ROBOT_HOST and ROBOT_TOKEN or pass --host and --token")
    curses.wrapper(control, args.host, args.token)


if __name__ == "__main__":
    main()
