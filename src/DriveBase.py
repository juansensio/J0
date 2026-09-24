"""Open-loop left/right drive with an independent command timeout."""

import micropython
import time
from machine import Timer


class DriveBase:
    def __init__(self, left_motors, right_motors, timeout_ms=750):
        if not left_motors or not right_motors:
            raise ValueError("both sides need at least one motor")
        if timeout_ms < 500 or timeout_ms > 1000:
            raise ValueError("timeout_ms must be between 500 and 1000")

        self.left_motors = tuple(left_motors)
        self.right_motors = tuple(right_motors)
        self.timeout_ms = timeout_ms
        self.timed_out = False
        self._active = False
        self._timeout_queued = False
        self._last_command_ms = time.ticks_ms()
        self._scheduled_timeout = self._stop_if_expired
        self.stop()
        self._timer = Timer(0)
        self._timer.init(period=50, mode=Timer.PERIODIC, callback=self._check_timeout)

    @staticmethod
    def _apply(motors, speed):
        duty = int(abs(speed) * 65535)
        for motor in motors:
            if speed > 0:
                motor.forward(duty)
            elif speed < 0:
                motor.reverse(duty)
            else:
                motor.stop()

    def set(self, left, right):
        if not (-1 <= left <= 1 and -1 <= right <= 1):
            raise ValueError("left and right must be in [-1, 1]")
        self._last_command_ms = time.ticks_ms()
        self.timed_out = False
        self._active = left != 0 or right != 0
        self._apply(self.left_motors, left)
        self._apply(self.right_motors, right)

    def stop(self):
        self._active = False
        for motor in self.left_motors + self.right_motors:
            motor.stop()

    def forward(self, speed=0.75):
        self.set(speed, speed)

    def reverse(self, speed=0.75):
        self.set(-speed, -speed)

    def left(self, speed=0.75):
        self.set(speed * 0.35, speed)

    def right(self, speed=0.75):
        self.set(speed, speed * 0.35)

    def spin_left(self, speed=0.75):
        self.set(-speed, speed)

    def spin_right(self, speed=0.75):
        self.set(speed, -speed)

    def _check_timeout(self, _timer):
        if self._active and not self._timeout_queued:
            if time.ticks_diff(time.ticks_ms(), self._last_command_ms) >= self.timeout_ms:
                self._timeout_queued = True
                try:
                    micropython.schedule(self._scheduled_timeout, 0)
                except RuntimeError:
                    # A full scheduler queue gets another chance on the next tick.
                    self._timeout_queued = False

    def _stop_if_expired(self, _arg):
        self._timeout_queued = False
        if self._active and time.ticks_diff(time.ticks_ms(), self._last_command_ms) >= self.timeout_ms:
            self.stop()
            self.timed_out = True
            print("DriveBase watchdog timeout: stopped")

    def close(self):
        self.stop()
        self._timer.deinit()
