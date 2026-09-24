"""Brief, one-wheel-at-a-time check for the four DRV8833 outputs."""

import time

from src.Motor import Motor


# Keep these pairs aligned with the connections in main.py.
MOTOR_PINS = (
    ("front right", 48, 45),
    ("rear left", 2, 1),
    ("rear right", 21, 47),
    ("front left", 41, 42),
)

DUTY = 65535
RUN_SECONDS = 0.75

motors = [(name, Motor(in1, in2)) for name, in1, in2 in MOTOR_PINS]

try:
    for name, motor in motors:
        for direction in ("forward", "reverse"):
            print(name, direction)
            getattr(motor, direction)(DUTY)
            time.sleep(RUN_SECONDS)
            motor.stop()
            time.sleep(0.25)
finally:
    for _, motor in motors:
        motor.stop()
    print("All motors stopped")
