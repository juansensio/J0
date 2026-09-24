# J0

J0 is a 4-wheeled robot

## Mark 0

- The Mark 0 prototype is a 4-wheeled robot with a single motor per wheel.
- Two DRV8833 motor drivers are used to control the motors.
- The ESP32-S3 is used to control the motors and read the encoders.
- Robot can move forward and backward, turn left and right, and spin in place.

![Mark 0](docs/M0.gif)

[See full video](docs/M0.mp4)

### Wi-Fi control

`src/DriveBase.py` groups the two left and two right motors. `set(left, right)`
accepts normalized speeds from -1 to 1; positive values use each motor's
forward direction. `forward`, `reverse`, `left`, `right`, and `stop` are shortcuts.
Left and right use a slower inner side, so they make moving turns.

The 750 ms watchdog stops both sides if a moving command is no longer
refreshed. At boot, `main.py` leaves the motors stopped, connects to Wi-Fi,
and waits for HTTP commands. `/forward` and `/backward` move for one second;
`/demo` moves forward for one second, pauses for half a second, then reverses
for one second. `/stop` interrupts any maneuver. `/reset` stops the motors and
restarts the ESP32-S3. A network loss also stops the motors.

1. Copy `wifi_config.example.py` to `wifi_config.py` and fill in the Wi-Fi
   credentials and a long, random `CONTROL_TOKEN`. The private config is
   ignored by Git.
2. Secure the robot with its wheels clear of the ground, connect the ESP32-S3
   by USB, and run `make deploy`. This installs the code and restarts the board.
3. Read the `Robot IP:` address from the serial output (`make repl`). On the
   Mac, set `ROBOT_HOST` to that address and `ROBOT_TOKEN` to the configured
   token. Then run `make status`, `make demo`, `make forward`,
   `make backward`, `make stop`, or `make reset`. Example:

   ```sh
   ROBOT_HOST=192.168.1.123 ROBOT_TOKEN=your-token make demo
   ```

   The equivalent direct request is
   `curl -H "X-Robot-Token: your-token" http://192.168.1.123/demo`.

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
