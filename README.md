# J0

J0 is a 4-wheeled robot

## Mark 0

- The Mark 0 prototype is a 4-wheeled robot with a single motor per wheel.
- Two DRV8833 motor drivers are used to control the motors.
- The ESP32-S3 is used to control the motors and read the encoders.
- Robot can move forward and backward, turn left and right, and spin in place.

![Mark 0](docs/M0.gif)

[See full video](docs/M0.mp4)

## Mark 1

- Added more maneuver commands: turn left and right, and spin in place.
- Added Wi-Fi control.
- Implemented simple cli client to control the robot.
- Added webrepl to update code wirelessly.
- Added wireless logging from the robot.
- Added simple HTML client to control the robot.

> With wifi controls and webrepl no need to physically connect to the robot. Both code and control are done wirelessly now :)

![Mark 1](docs/M1.gif)

[See full video](docs/M1.mp4)

### Wi-Fi control

`src/DriveBase.py` groups the two left and two right motors. `set(left, right)`
accepts normalized speeds from -1 to 1; positive values use each motor's
forward direction. `forward`, `reverse`, `left`, `right`, and `stop` are shortcuts.
Left and right use a slower inner side, so they make moving turns.

The 750 ms watchdog stops both sides if a moving command is no longer
refreshed. `boot.py` connects to Wi-Fi and starts WebREPL before `main.py`
starts the HTTP server with the motors stopped. `/forward`, `/backward`, `/left`,
and `/right` each move for one second. `/spin_left` and `/spin_right` each move
for two seconds, driving the two sides in opposite directions. `/demo` runs all
six in that order, with a half-second stop between moves. `/stop` interrupts any
maneuver. `/reset` stops the motors and restarts the ESP32-S3. A network loss
also stops the motors. Turns and spins are open-loop, so their actual angle
depends on the floor and battery charge.

1. Copy `wifi_config.example.py` to `wifi_config.py` and fill in the Wi-Fi
   credentials and a long, random `CONTROL_TOKEN`. The private config is
   ignored by Git.
2. Secure the robot with its wheels clear of the ground, connect the ESP32-S3
   by USB, and run `make deploy-usb` once. This installs `boot.py`, the private
   Wi-Fi config, and the application. Run `import webrepl_setup` from the serial
   REPL to enable WebREPL and set its password if you have not already done so.
3. Read the `Robot IP:` address from the serial output (`make repl`). On the
   Mac, set `ROBOT_HOST` to that address and `ROBOT_TOKEN` to the configured
   token. Then run `make status`, `make demo`, `make forward`,
   `make backward`, `make left`, `make right`, `make spin_left`,
   `make spin_right`, `make stop`, or `make reset`. Example:

   ```sh
   ROBOT_HOST=192.168.1.123 ROBOT_TOKEN=your-token make demo
   ```

   The equivalent direct request is
   `curl -H "X-Robot-Token: your-token" http://192.168.1.123/demo`.

For later wireless updates, put `WEBREPL_PASSWORD`, `ROBOT_HOST`, and
`ROBOT_TOKEN` in `.env` (ignored by Git), then run `make deploy`. This uploads
every `src/*.py` file and `main.py` over WebREPL
on port 8266, then calls the authenticated HTTP `/reset` endpoint. `src/`
must already exist on the board from the first USB deployment. Keep WebREPL
configured on the board; its password lives in `webrepl_cfg.py`, which the
wireless deploy does not replace. Leave the browser WebREPL client disconnected
while uploading, since WebREPL supports one connection at a time.

```sh
make deploy
```

For browser control, run `python client.py` on your Mac after setting
`ROBOT_HOST` and `ROBOT_TOKEN` as above. It prints the full URL to open on a
phone connected to the same Wi-Fi. On the Mac, open `http://localhost:8000/`.
Tap the movement, spin, demo, or stop buttons. Each movement tap lasts one second;
spins last two seconds. The page listens on `0.0.0.0` so your phone can reach
it. Anyone on the same network who can open the page can control the robot while
the client is running. You can also pass `--host`, `--token`, and `--port` directly.

For terminal control, run `python cli.py` (or `make cli`) with the same
`ROBOT_HOST` and `ROBOT_TOKEN`. Use the arrow keys to move, Space to stop, and Q
to quit. Each arrow press starts a one-second move; quitting sends a stop
command. The web and terminal clients can run together. The robot follows the
most recent command from either client, and Stop interrupts either one.

### Remote logs

Set `LOG_HOST` in `wifi_config.py` to your Mac's IP address on the robot's
Wi-Fi network. `LOG_PORT` defaults to `9999`; set it in the same file if you
need another port. Run `make deploy-usb` after changing `wifi_config.py`,
because wireless `make deploy` does not upload the private config. On the Mac,
start the receiver before running commands:

```sh
make logs
```

Use `make logs LOG_PORT=10000` if you changed the port on the robot. The
receiver shows the arrival time, robot IP, severity, component, and message.
Boot, server, motion transitions, watchdog stops, and network errors are
logged to the serial/WebREPL console and sent as best-effort UDP packets.
Messages may be lost if Wi-Fi is down or the receiver is not running. If
`LOG_HOST` is missing or `None`, logging stays on the console only.

Other modules can use the same logger:

```python
from src.logger import get_logger

log = get_logger("battery")
log.info("voltage", 7.4)
log.warning("battery low")
```

Keep the robot on a trusted local network: these commands use plain HTTP.
`make test` runs the local logic checks. A fully hung controller still needs
a physical reset or power cycle.

## Goal

The resulting physical architecture is exactly what I want to simulate:

```
                     ┌──────────────────────┐
                     │        Mac           │
                     │ ROS 2 Jazzy          │
                     │                      │
                     │ SLAM / Nav2          │
                     │ robot_state_pub      │
                     │ odometry fusion      │
                     └──────────┬───────────┘
                                │
                              Wi-Fi
                                │
                     ┌──────────▼───────────┐
                     │     ESP32-S3         │
                     │                      │
               ┌─────┤ wheel PID           ├─────┐
               │     │ encoder counting    │     │
               │     │ IMU                 │     │
               │     │ LiDAR bridge        │     │
               │     └──────────────────────┘     │
               ▼                                  ▼
           MDD3A                              LD19
          /     \
     motor L   motor R
        ↑         ↑
    encoder    encoder
```

And Gazebo will expose essentially the same interfaces:

```
             SIMULATION              REAL

/cmd_vel  → Gazebo drive        → ESP32 PID
/odom     ← Gazebo encoders     ← real encoders
/imu/data ← Gazebo IMU          ← MPU6050
/scan     ← Gazebo LiDAR        ← LD19

              ↓ same ↓

          SLAM Toolbox
              +
             Nav2
```

That gives us a very clean milestone: first make the virtual J0 map and navigate, then switch sim.launch.py → real.launch.py and progressively make the physical machine reproduce the same behavior.
