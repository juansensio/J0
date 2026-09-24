import time

from src.Motor import Motor

RLW_IN1 = 21
RLW_IN2 = 47
FLW_IN1 = 48
FLW_IN2 = 45
RRW_IN1 = 41
RRW_IN2 = 42
FRW_IN1 = 2
FRW_IN2 = 1

FLM = Motor(FLW_IN1, FLW_IN2)
FRM = Motor(FRW_IN1, FRW_IN2)
RLM = Motor(RLW_IN1, RLW_IN2)
RRM = Motor(RRW_IN1, RRW_IN2)

duty = 32768  # 50% of the 16-bit PWM range


def stop():
    FLM.stop()
    RLM.stop()
    FRM.stop()
    RRM.stop()


def forward():
    FLM.forward(duty)
    RLM.forward(duty)
    FRM.forward(duty)
    RRM.forward(duty)


def reverse():
    FLM.reverse(duty)
    RLM.reverse(duty)
    FRM.reverse(duty)
    RRM.reverse(duty)


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
