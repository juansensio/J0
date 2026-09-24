from machine import Pin, PWM


class Motor:
    def __init__(self, in1: Pin, in2: Pin):
        self.in1 = PWM(in1, freq=2000, duty_u16=0)
        self.in2 = PWM(in2, freq=2000, duty_u16=0)

    def stop(self):
        self.in1.duty_u16(0)
        self.in2.duty_u16(0)

    def forward(self, duty: int):
        self.in1.duty_u16(duty)
        self.in2.duty_u16(0)

    def reverse(self, duty: int):
        self.in1.duty_u16(0)
        self.in2.duty_u16(duty)
