"""Start J0's Wi-Fi command server. Motors stay stopped until commanded."""

import time

from src.DriveBase import DriveBase
from src.Motor import Motor
from src.RobotServer import RobotServer
from wifi_config import WIFI_SSID, WIFI_PASSWORD, CONTROL_TOKEN


LEFT_PINS = ((2, 1), (41, 42))       # rear left, front left
RIGHT_PINS = ((48, 45), (21, 47))   # front right, rear right
motors = []
drive = None
server = None


try:
    for pins in LEFT_PINS + RIGHT_PINS:
        motors.append(Motor(*pins))
    drive = DriveBase(motors[:2], motors[2:])
    server = RobotServer(drive, WIFI_SSID, WIFI_PASSWORD, CONTROL_TOKEN)
    while True:
        try:
            server.run()
        except OSError as exc:
            print("Network error:", exc)
            drive.stop()
            time.sleep(2)
finally:
    if server is not None:
        server.close()
    if drive is not None:
        drive.close()
    else:
        for motor in motors:
            motor.stop()
