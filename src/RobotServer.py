"""Small HTTP controller for short, interruptible open-loop maneuvers."""

import machine
import network
import select
import socket
import time
from src.logger import get_logger


log = get_logger("RobotServer")


class RobotServer:
    TICK_MS = 50
    MOVE_MS = 1000
    SPIN_MS = 2000
    DEMO_PAUSE_MS = 500
    COMMANDS = {
        b"/forward": "forward",
        b"/backward": "reverse",
        b"/left": "left",
        b"/right": "right",
        b"/spin_left": "spin_left",
        b"/spin_right": "spin_right",
    }
    DEMO_COMMANDS = ("forward", "reverse", "left", "right",
                     "spin_left", "spin_right")

    def __init__(self, drive, ssid, password, token):
        if not ssid or not token:
            raise ValueError("WIFI_SSID and CONTROL_TOKEN are required")
        self.drive = drive
        self.ssid = ssid
        self.password = password
        self.token = token
        self.wlan = network.WLAN(network.WLAN.IF_STA)
        self.listener = None
        self.steps = ()
        self.step_index = 0
        self.step_started = 0
        self.last_refresh = 0

    def connect(self):
        self.drive.stop()
        self.wlan.active(True)
        if not self.wlan.isconnected():
            self.wlan.connect(self.ssid, self.password)
            started = time.ticks_ms()
            while not self.wlan.isconnected():
                if time.ticks_diff(time.ticks_ms(), started) >= 15000:
                    raise OSError("Wi-Fi connection timed out")
                time.sleep_ms(100)
        log.info("Robot IP:", self.wlan.ifconfig()[0])

    def run(self):
        self.drive.stop()
        self.connect()
        listener = socket.socket()
        self.listener = listener
        try:
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listener.bind(("0.0.0.0", 80))
            listener.listen(1)
            poller = select.poll()
            poller.register(listener, select.POLLIN)
            log.info("J0 ready")
            while True:
                self._tick()
                if not self.wlan.isconnected():
                    raise OSError("Wi-Fi disconnected")
                if not poller.poll(self.TICK_MS):
                    continue
                conn, _ = listener.accept()
                try:
                    conn.settimeout(0.2)
                    self._handle(conn)
                finally:
                    conn.close()
        finally:
            self.drive.stop()
            listener.close()
            self.listener = None

    def _start(self, steps):
        self.drive.stop()
        self.steps = steps
        self.step_index = 0
        self.step_started = time.ticks_ms()
        self.last_refresh = self.step_started
        self._apply_step(announce=True)

    def _apply_step(self, announce=False):
        name, _ = self.steps[self.step_index]
        if name == "stop":
            self.drive.stop()
        else:
            getattr(self.drive, name)()
        if announce:
            log.info("step", name)

    def _stop(self):
        was_running = bool(self.steps)
        self.steps = ()
        self.drive.stop()
        if was_running:
            log.info("stopped")

    def _tick(self):
        if not self.steps:
            return
        now = time.ticks_ms()
        _, duration = self.steps[self.step_index]
        if time.ticks_diff(now, self.step_started) >= duration:
            self.step_index += 1
            if self.step_index == len(self.steps):
                self._stop()
                return
            self.step_started = now
            self._apply_step(announce=True)
        elif time.ticks_diff(now, self.last_refresh) >= 100:
            self._apply_step()
            self.last_refresh = now

    def _handle(self, conn):
        request = conn.recv(1024)
        lines = request.split(b"\r\n")
        first = lines[0].split() if lines else []
        if len(first) != 3 or first[0] != b"GET":
            return self._reply(conn, 400, "Bad request")
        path = first[1]
        expected = self.token.encode()
        authorized = any(line.split(b":", 1)[1].strip() == expected
                         for line in lines[1:]
                         if line.split(b":", 1)[0].lower() == b"x-robot-token"
                         and b":" in line)
        if not authorized:
            return self._reply(conn, 403, "Forbidden")
        if path == b"/":
            return self._reply(conn, 200, "Robot alive")
        if path == b"/stop":
            self._stop()
            return self._reply(conn, 200, "Stopped")
        if path in self.COMMANDS:
            command = self.COMMANDS[path]
            duration = self.SPIN_MS if command in ("spin_left", "spin_right") else self.MOVE_MS
            self._start(((command, duration),))
            seconds = duration // 1000
            unit = "second" if seconds == 1 else "seconds"
            return self._reply(conn, 200, "Motion started for %d %s" % (seconds, unit))
        if path == b"/demo":
            steps = []
            for name in self.DEMO_COMMANDS:
                if steps:
                    steps.append(("stop", self.DEMO_PAUSE_MS))
                duration = self.SPIN_MS if name in ("spin_left", "spin_right") else self.MOVE_MS
                steps.append((name, duration))
            self._start(steps)
            return self._reply(conn, 200, "Demo started")
        if path == b"/reset":
            self._stop()
            log.info("reset requested")
            self._reply(conn, 200, "Resetting")
            conn.close()
            # Give the TCP response time to leave before restarting Wi-Fi.
            time.sleep_ms(100)
            machine.reset()
            return
        return self._reply(conn, 404, "Unknown command")

    @staticmethod
    def _reply(conn, status, message):
        body = message.encode()
        reason = {200: "OK", 400: "Bad Request", 403: "Forbidden",
                  404: "Not Found"}[status]
        conn.sendall(("HTTP/1.1 %d %s\r\nContent-Type: text/plain\r\n"
                      "Content-Length: %d\r\nConnection: close\r\n\r\n" %
                      (status, reason, len(body))).encode() + body)

    def close(self):
        self._stop()
        if self.listener is not None:
            self.listener.close()
            self.listener = None
