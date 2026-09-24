from machine import Pin, PWM
from time import sleep

PIN_IN1 = 1
PIN_IN2 = 42
MOTOR_DUTY = 32768  # 50% of the 16-bit PWM range


def run_motor_test():
    # boot.py has already held both pins low during the LED and buzzer step.
    in1 = PWM(Pin(PIN_IN1), freq=2000, duty_u16=0)
    in2 = PWM(Pin(PIN_IN2), freq=2000, duty_u16=0)

    def stop():
        in1.duty_u16(0)
        in2.duty_u16(0)

    try:
        print("Motor forward at 50%")
        in2.duty_u16(0)
        in1.duty_u16(MOTOR_DUTY)
        sleep(1)
        stop()

        print("Motor stopped")
        sleep(1)

        print("Motor reverse at 50%")
        in1.duty_u16(0)
        in2.duty_u16(MOTOR_DUTY)
        sleep(1)
    finally:
        stop()
        in1.deinit()
        in2.deinit()
        # PWM deinit releases the pins; hold both low after the test.
        Pin(PIN_IN1, Pin.OUT, value=0)
        Pin(PIN_IN2, Pin.OUT, value=0)

    print("Motor test complete; motor stopped")
