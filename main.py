import time

from src.Motor import Motor

RLW_IN1 = 47
RLW_IN2 = 21
FLW_IN1 = 48
FLW_IN2 = 45
RRW_IN1 = 41
RRW_IN2 = 42
FRW_IN1 = 2
FRW_IN2 = 1

FML = Motor(FLW_IN1, FLW_IN2)
FMR = Motor(FRW_IN1, FRW_IN2)
RML = Motor(RLW_IN1, RLW_IN2)
RMR = Motor(RRW_IN1, RRW_IN2)

duty = 32768  # 50% of the 16-bit PWM range


def stop():
    FML.stop()
    FMR.stop()
    RML.stop()
    RMR.stop()


def forward():
    FML.forward(duty)
    FMR.forward(duty)
    RML.forward(duty)
    RMR.forward(duty)


def reverse():
    FML.reverse(duty)
    FMR.reverse(duty)
    RML.reverse(duty)
    RMR.reverse(duty)


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
