import time

from src.Motor import Motor

MOTOR_PINS = (
    ("front right", 48, 45),
    ("rear left", 2, 1),
    ("rear right", 21, 47),
    ("front left", 41, 42),
)

DUTY = int(0.75 * 65535)  # Match the working motor diagnostic during startup.


motors = [(name, Motor(in1, in2)) for name, in1, in2 in MOTOR_PINS]


def stop():
    for _, motor in motors:
        motor.stop()


def forward():
    for _, motor in motors:
        motor.forward(DUTY)


def reverse():
    for _, motor in motors:
        motor.reverse(DUTY)


try:
    print("Stopping")
    stop()
    time.sleep(1)
    print("Forwarding")
    forward()
    time.sleep(1)
    stop()
    time.sleep(0.25)
    print("Reversing")
    reverse()
    time.sleep(1)
finally:
    print("Stopping")
    stop()
