import time


def flash_led(led):
    print("LED starts flashing...")
    led[0] = (0, 0, 0)
    led.write()
    time.sleep(0.5)
    led[0] = (255, 0, 0)
    led.write()
    time.sleep(0.5)
    led[0] = (0, 255, 0)
    led.write()
    time.sleep(0.5)
    led[0] = (0, 0, 255)
    led.write()
    time.sleep(1.5)
