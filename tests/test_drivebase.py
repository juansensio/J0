import importlib
import sys
import time
import types
import unittest
from unittest.mock import patch


class FakeMotor:
    def __init__(self):
        self.direction = "stop"
        self.duty = 0

    def forward(self, duty):
        self.direction, self.duty = "forward", duty

    def reverse(self, duty):
        self.direction, self.duty = "reverse", duty

    def stop(self):
        self.direction, self.duty = "stop", 0


class FakeTimer:
    PERIODIC = 1

    def __init__(self, timer_id):
        self.timer_id = timer_id
        self.closed = False

    def init(self, **kwargs):
        self.settings = kwargs

    def fire(self):
        self.settings["callback"](self)

    def deinit(self):
        self.closed = True


class DriveBaseTest(unittest.TestCase):
    def setUp(self):
        self.now = 0
        self.clock = patch.multiple(
            time,
            ticks_ms=lambda: self.now,
            ticks_diff=lambda a, b: a - b,
            create=True,
        )
        self.clock.start()
        self.addCleanup(self.clock.stop)
        fake_machine = types.ModuleType("machine")
        fake_machine.Timer = FakeTimer
        fake_micropython = types.ModuleType("micropython")
        fake_micropython.schedule = lambda callback, arg: callback(arg)
        modules = patch.dict(sys.modules, machine=fake_machine, micropython=fake_micropython)
        modules.start()
        self.addCleanup(modules.stop)
        sys.modules.pop("src.DriveBase", None)
        self.DriveBase = importlib.import_module("src.DriveBase").DriveBase
        self.left = [FakeMotor(), FakeMotor()]
        self.right = [FakeMotor(), FakeMotor()]
        self.drive = self.DriveBase(self.left, self.right)
        self.addCleanup(self.drive.close)

    def test_commands_control_the_correct_sides(self):
        cases = (
            ("forward", "forward", "forward", "equal"),
            ("reverse", "reverse", "reverse", "equal"),
            ("left", "forward", "forward", "left_slower"),
            ("right", "forward", "forward", "right_slower"),
            ("spin_left", "reverse", "forward", "equal"),
            ("spin_right", "forward", "reverse", "equal"),
        )
        for command, left_dir, right_dir, speeds in cases:
            getattr(self.drive, command)()
            self.assertTrue(all(m.direction == left_dir for m in self.left))
            self.assertTrue(all(m.direction == right_dir for m in self.right))
            if speeds == "equal":
                self.assertEqual(self.left[0].duty, self.right[0].duty)
            elif speeds == "left_slower":
                self.assertLess(self.left[0].duty, self.right[0].duty)
            else:
                self.assertGreater(self.left[0].duty, self.right[0].duty)
        self.drive.stop()
        self.assertTrue(all(m.direction == "stop" for m in self.left + self.right))

    def test_normalized_set_and_invalid_values(self):
        self.drive.set(-1, 0)
        self.assertEqual(self.left[0].direction, "reverse")
        self.assertEqual(self.left[0].duty, 65535)
        self.assertEqual(self.right[0].direction, "stop")
        with self.assertRaises(ValueError):
            self.drive.set(1.1, 0)

    def test_watchdog_stops_only_after_command_expires(self):
        self.drive.forward()
        self.now = 700
        self.drive._timer.fire()
        self.assertFalse(self.drive.timed_out)
        self.drive.forward()  # refresh at 700 ms
        self.now = 1449
        self.drive._timer.fire()
        self.assertFalse(self.drive.timed_out)
        self.now = 1450
        self.drive._timer.fire()
        self.assertTrue(self.drive.timed_out)
        self.assertTrue(all(m.direction == "stop" for m in self.left + self.right))
        self.drive.forward()
        self.assertFalse(self.drive.timed_out)
        self.drive.stop()
        self.now = 3000
        self.drive._timer.fire()
        self.assertFalse(self.drive.timed_out)


if __name__ == "__main__":
    unittest.main()
