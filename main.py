"""Start J0's Wi-Fi command server. Motors stay stopped until commanded."""

import time

from src.DriveBase import DriveBase
from src.Motor import Motor
from src.RobotServer import RobotServer
from src.logger import configure, get_logger
import wifi_config


LEFT_PINS = ((2, 1), (41, 42))  # rear left, front left
RIGHT_PINS = ((48, 45), (21, 47))  # front right, rear right
motors = []
drive = None
server = None
configure(getattr(wifi_config, "LOG_HOST", None),
          getattr(wifi_config, "LOG_PORT", 9999))
log = get_logger("main")


try:
    for pins in LEFT_PINS + RIGHT_PINS:
        motors.append(Motor(*pins))
    drive = DriveBase(motors[:2], motors[2:])
    server = RobotServer(drive, wifi_config.WIFI_SSID,
                         wifi_config.WIFI_PASSWORD, wifi_config.CONTROL_TOKEN)
    while True:
        try:
            server.run()
        except OSError as exc:
            drive.stop()
            log.error("Network error:", exc)
            time.sleep(2)
finally:
    if server is not None:
        server.close()
    if drive is not None:
        drive.close()
    else:
        for motor in motors:
            motor.stop()
