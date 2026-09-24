import time

from src.Motor import Motor

MOTOR_PINS = (
    ("front right", 48, 45),
    ("rear left", 2, 1),
    ("rear right", 21, 47),
    ("front left", 41, 42),
)

DUTY = 65535 // 2


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


print("Stopping")
stop()
time.sleep(1)
print("Forwarding")
forward()
time.sleep(1)
print("Reversing")
reverse()
time.sleep(1)
print("Stopping")
stop()
