"""Serve a small browser controller for J0 on the local Wi-Fi network."""

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os
import socket
import urllib.error
import urllib.request


COMMANDS = frozenset({
    "forward", "backward", "left", "right", "spin_left", "spin_right",
    "stop", "demo",
})

PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>J0 robot control</title>
  <style>
    :root { font-family: system-ui, sans-serif; color-scheme: light dark; }
    body { max-width: 420px; margin: 0 auto; padding: 20px; text-align: center; }
    h1 { margin: 12px 0 4px; }
    p { margin: 6px 0 20px; }
    .controls { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
    button { min-height: 72px; font: inherit; font-size: 1.1rem; border-radius: 14px;
             border: 1px solid #888; cursor: pointer; touch-action: manipulation; }
    button:active { transform: scale(.96); }
    .forward { grid-column: 2; }
    .left { grid-column: 1; grid-row: 2; }
    .stop { grid-column: 2; grid-row: 2; background: #c62828; color: white; font-weight: bold; }
    .right { grid-column: 3; grid-row: 2; }
    .backward { grid-column: 2; grid-row: 3; }
    .extras { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: 16px; }
    #status { min-height: 1.5em; margin-top: 20px; }
  </style>
</head>
<body>
  <h1>J0 control</h1>
  <p>Tap once to move for 1 second. Spins last 2 seconds. Stop interrupts any move.</p>
  <div class="controls">
    <button class="forward" data-command="forward">▲<br>Forward</button>
    <button class="left" data-command="left">◀<br>Left</button>
    <button class="stop" data-command="stop">■<br>Stop</button>
    <button class="right" data-command="right">▶<br>Right</button>
    <button class="backward" data-command="backward">▼<br>Back</button>
  </div>
  <div class="extras">
    <button data-command="spin_left">↶<br>Spin left</button>
    <button data-command="demo">Demo</button>
    <button data-command="spin_right">↷<br>Spin right</button>
  </div>
  <p id="status" role="status" aria-live="polite">Ready</p>
  <script>
    const status = document.getElementById('status');
    document.querySelectorAll('[data-command]').forEach(button => {
      button.addEventListener('click', async () => {
        const command = button.dataset.command;
        status.textContent = 'Sending ' + command.replace('_', ' ') + '…';
        try {
          const response = await fetch('/api/' + command, {
            method: 'POST',
            headers: { 'X-Requested-With': 'J0-control' }
          });
          const message = await response.text();
          status.textContent = response.ok ? message : 'Error: ' + message;
        } catch (error) {
          status.textContent = 'Connection error: ' + error.message;
        }
      });
    });
  </script>
</body>
</html>
""".encode("utf-8")


def send_command(host, token, command):
    request = urllib.request.Request(
        f"http://{host}/{command}", headers={"X-Robot-Token": token}
    )
    with urllib.request.urlopen(request, timeout=2) as response:
        return response.read().decode("utf-8", errors="replace")


def phone_url(robot_host, port):
    """Find the Mac address used to reach the robot on the local network."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
        probe.connect((robot_host, 80))
        address = probe.getsockname()[0]
    return f"http://{address}:{port}/"


def make_handler(robot_host, token):
    class ControlHandler(BaseHTTPRequestHandler):
        def reply(self, status, body, content_type="text/plain; charset=utf-8"):
            if isinstance(body, str):
                body = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == "/":
                self.reply(200, PAGE, "text/html; charset=utf-8")
            else:
                self.reply(404, "Not found")

        def do_POST(self):
            if self.headers.get("X-Requested-With") != "J0-control":
                self.reply(403, "Forbidden")
                return
            command = self.path.removeprefix("/api/")
            if not self.path.startswith("/api/") or command not in COMMANDS:
                self.reply(404, "Unknown command")
                return
            try:
                self.reply(200, send_command(robot_host, token, command))
            except (OSError, urllib.error.URLError, ValueError) as exc:
                self.reply(502, f"Robot connection failed: {exc}")

    return ControlHandler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=os.getenv("ROBOT_HOST"), help="robot IP address")
    parser.add_argument("--token", default=os.getenv("ROBOT_TOKEN"), help="control token")
    parser.add_argument("--port", type=int, default=8000, help="web page port (default: 8000)")
    args = parser.parse_args()
    if not args.host or not args.token:
        parser.error("set ROBOT_HOST and ROBOT_TOKEN or pass --host and --token")
    server = ThreadingHTTPServer(("0.0.0.0", args.port), make_handler(args.host, args.token))
    print(f"J0 controls: http://localhost:{server.server_port}/")
    try:
        print(f"On your phone, open {phone_url(args.host, server.server_port)}")
    except OSError as exc:
        print(f"Could not detect the Mac's network address: {exc}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
