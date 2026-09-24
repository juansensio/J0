from machine import Pin, PWM


class Motor:
    def __init__(self, in1: int, in2: int):
        self.in1 = PWM(Pin(in1, Pin.OUT, value=0), freq=2000, duty_u16=0)
        self.in2 = PWM(Pin(in2, Pin.OUT, value=0), freq=2000, duty_u16=0)

    def stop(self):
        self.in1.duty_u16(0)
        self.in2.duty_u16(0)

    def forward(self, duty: int):
        self.in2.duty_u16(0)
        self.in1.duty_u16(duty)

    def reverse(self, duty: int):
        self.in1.duty_u16(0)
        self.in2.duty_u16(duty)
