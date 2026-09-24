import importlib
import sys
import time
import types
import unittest
from unittest.mock import patch


class FakeDrive:
    def __init__(self):
        self.commands = []

    def stop(self):
        self.commands.append("stop")

    def forward(self):
        self.commands.append("forward")

    def reverse(self):
        self.commands.append("reverse")

    def left(self):
        self.commands.append("left")

    def right(self):
        self.commands.append("right")

    def spin_left(self):
        self.commands.append("spin_left")

    def spin_right(self):
        self.commands.append("spin_right")


class FakeConnection:
    def __init__(self, request):
        self.request = request
        self.response = b""
        self.closed = False

    def recv(self, _size):
        return self.request

    def sendall(self, data):
        self.response += data

    def close(self):
        self.closed = True


class RobotServerTest(unittest.TestCase):
    def setUp(self):
        self.now = 0
        clock = patch.multiple(time, ticks_ms=lambda: self.now,
                               ticks_diff=lambda a, b: a - b,
                               sleep_ms=lambda _: None, create=True)
        clock.start()
        self.addCleanup(clock.stop)
        machine = types.ModuleType("machine")
        machine.reset = lambda: None
        network = types.ModuleType("network")
        class FakeWLAN:
            IF_STA = 0

            def __init__(self, _kind):
                pass

        network.WLAN = FakeWLAN
        modules = patch.dict(sys.modules, machine=machine, network=network)
        modules.start()
        self.addCleanup(modules.stop)
        sys.modules.pop("src.RobotServer", None)
        self.RobotServer = importlib.import_module("src.RobotServer").RobotServer
        self.drive = FakeDrive()
        self.server = self.RobotServer(self.drive, "ssid", "password", "CaseSensitive")

    def request(self, path, token="CaseSensitive"):
        header = (b"X-Robot-Token: " + token.encode() + b"\r\n") if token else b""
        conn = FakeConnection(b"GET " + path.encode() + b" HTTP/1.1\r\n" + header + b"\r\n")
        self.server._handle(conn)
        return conn.response

    def test_demo_advances_and_stop_interrupts(self):
        self.assertIn(b"200 OK", self.request("/demo"))
        self.assertEqual(self.drive.commands[-1], "forward")
        self.now = 100
        self.server._tick()
        self.assertEqual(self.drive.commands[-1], "forward")
        self.now = 1000
        self.server._tick()
        self.assertEqual(self.drive.commands[-1], "stop")
        self.now = 1500
        self.server._tick()
        self.assertEqual(self.drive.commands[-1], "reverse")
        self.assertIn(b"200 OK", self.request("/stop"))
        self.now = 3000
        self.server._tick()
        self.assertEqual(self.drive.commands[-1], "stop")
        self.assertFalse(self.server.steps)

    def test_commands_are_exact_and_require_token(self):
        self.assertIn(b"Robot alive", self.request("/"))
        self.assertIn(b"403 Forbidden", self.request("/forward", "wrong"))
        self.assertIn(b"403 Forbidden", self.request("/forward", ""))
        self.assertIn(b"404 Not Found", self.request("/forward-extra"))
        self.assertNotIn("forward", self.drive.commands)
        self.assertIn(b"200 OK", self.request("/backward"))
        self.assertEqual(self.drive.commands[-1], "reverse")
        self.now = 1000
        self.server._tick()
        self.assertEqual(self.drive.commands[-1], "stop")

    def test_each_turn_and_spin_command_stops_after_one_second(self):
        for path, command in (("/left", "left"), ("/right", "right"),
                              ("/spin_left", "spin_left"),
                              ("/spin_right", "spin_right")):
            self.assertIn(b"200 OK", self.request(path))
            self.assertEqual(self.drive.commands[-1], command)
            self.now += 1000
            self.server._tick()
            self.assertEqual(self.drive.commands[-1], "stop")

    def test_demo_runs_all_directions_with_stops_between(self):
        self.request("/demo")
        observed = [self.drive.commands[-1]]
        for index in range(1, 11):
            self.now += 1000 if index % 2 else 500
            self.server._tick()
            observed.append(self.drive.commands[-1])
        self.now += 1000
        self.server._tick()
        observed.append(self.drive.commands[-1])
        self.assertEqual(observed, ["forward", "stop", "reverse", "stop",
                                    "left", "stop", "right", "stop",
                                    "spin_left", "stop", "spin_right", "stop"])
        self.assertFalse(self.server.steps)

    def test_reset_stops_before_reset(self):
        machine = sys.modules["machine"]
        machine.reset = lambda: self.assertEqual(self.drive.commands[-1], "stop")
        self.request("/forward")
        self.assertIn(b"200 OK", self.request("/reset"))
        self.assertEqual(self.drive.commands[-1], "stop")


if __name__ == "__main__":
    unittest.main()
