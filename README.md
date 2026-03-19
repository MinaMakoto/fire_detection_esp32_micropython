# ESP32 Fire Suppression System

An autonomous fire detection and suppression system built on a plain ESP32 using MicroPython. The system continuously scans for fire and smoke, confirms detections against false positives, and activates a water pump and directional nozzle only when fire is genuinely verified.

---

## Table of Contents

1. [Hardware Overview](#1-hardware-overview)
2. [GPIO Pin Map](#2-gpio-pin-map)
3. [Device Roles](#3-device-roles)
4. [System States](#4-system-states)
5. [How the Devices Coordinate](#5-how-the-devices-coordinate)
6. [False-Positive Protection](#6-false-positive-protection)
7. [File Structure](#7-file-structure)
8. [Running the Tests](#8-running-the-tests)
9. [Flashing to ESP32](#9-flashing-to-esp32)
10. [Tuning Parameters](#10-tuning-parameters)

---

## 1. Hardware Overview

| Component | Purpose |
|---|---|
| ESP32 (plain, 38-pin) | Microcontroller — runs all logic |
| Servo Motor 1 (SG90 or similar) | Scans the environment for fire |
| Servo Motor 2 (SG90 or similar) | Aims the water nozzle during suppression |
| IR Flame Sensor | Detects infrared radiation from flames |
| MQ-2 Smoke/Gas Sensor | Detects smoke, LPG, propane |
| 5V Relay Module | Switches the water pump on/off |
| Water Pump (5V/12V DC) | Delivers water through the nozzle |
| Active/Passive Buzzer | Audio alerts for warning and danger states |
| DHT11 | Logs ambient temperature and humidity |
| Common-Cathode RGB LED | Visual indicator of system state |

---

## 2. GPIO Pin Map

```
GPIO26  →  Servo 1 (scanner)    PWM signal
GPIO23  →  Servo 2 (nozzle)     PWM signal
GPIO14  →  IR Flame Sensor      Digital input (D0)
GPIO27  →  Smoke Sensor         Digital input (D0)
GPIO5   →  Relay module         Digital output (IN pin)
GPIO21  →  Buzzer               PWM signal
GPIO13  →  DHT11                One-wire data
GPIO25  →  RGB LED Red          PWM signal
GPIO33  →  RGB LED Green        PWM signal
GPIO12  →  RGB LED Blue         PWM signal
```

> **Note on GPIO12:** This pin is sampled by the ESP32 at boot to set flash voltage. If the board fails to boot after wiring the blue channel, add a 10kΩ pull-down resistor on GPIO12 or reassign blue to another free GPIO.

---

## 3. Device Roles

### Servo 1 — Scanner
Servo 1 is mounted to rotate the IR flame sensor horizontally across a 0°–180° arc. In standby and warning states, it sweeps continuously at 2° per tick (20ms per tick), giving full angular coverage of the monitored area. When fire is confirmed, it **locks at the detection angle** — the heading where the fire was first confirmed — so the system knows where the fire is.

### Servo 2 — Nozzle
Servo 2 aims the water nozzle. It is **parked at 90° and completely inactive** in every state except active fire suppression. Once fire is verified (see Section 6), servo 2 moves to 0° and begins a slow 0°→180°→0° sweep at 2° per tick with 40ms between ticks. The slower speed (double the delay of servo 1) is deliberate: it gives the nozzle more time over each angle, resulting in greater water coverage per area. The pump runs throughout this sweep.

### IR Flame Sensor (D0 → GPIO14)
The flame sensor detects infrared radiation in the 760–1100 nm band emitted by open flames. Its D0 output goes **HIGH when a flame is within range**. The sensitivity is adjustable via the onboard potentiometer. In the system, the sensor is polled every loop iteration. Rather than acting on a single reading, the system requires **3 consecutive HIGH reads** before escalating — this is the primary false-positive filter.

### Smoke Sensor (D0 → GPIO27)
The MQ-2 detects smoke, LPG, propane, hydrogen, and methane. Its D0 output goes **HIGH when gas concentration exceeds the threshold** set by its onboard potentiometer. A smoke detection alone triggers the **WARNING state** — the LED turns yellow and the buzzer gives slow periodic beeps — but neither the pump nor servo 2 are activated. The smoke sensor acts as an early alert only.

### Relay Module (GPIO5)
The relay is the switch between the ESP32's 3.3V logic and the pump's higher-voltage supply. GPIO5 HIGH energises the relay coil (ACTIVE_HIGH mode), which closes the circuit and powers the pump. The relay is **de-energised at startup** and de-energised again immediately after the fire sensor clears. The `RELAY_ACTIVE_LOW` flag in `main.py` can be set to `True` for modules that trigger on LOW (some optocoupler-isolated boards).

### Buzzer (GPIO21)
The buzzer uses PWM to produce two distinct audio signals:
- **700 Hz, pulsed (100ms on / 700ms off)** — WARNING state, smoke detected
- **1500 Hz, continuous** — DANGER state, fire confirmed and pump running

`duty(512)` gives 50% duty cycle, which produces maximum loudness. `duty(0)` silences it completely.

### DHT11 (GPIO13)
The DHT11 logs temperature (°C) and humidity (%RH) to the serial console every 5 seconds using a non-blocking timer (`time.ticks_diff`). It does not influence any system state decisions — it is passive environmental logging. In future versions, high temperature readings could be cross-referenced with the flame sensor to improve confidence.

### RGB LED (GPIO25 / GPIO33 / GPIO12)
The LED provides instant visual feedback on system state using PWM-mixed colours:

| Colour          |     RGB Values   |      State                   |
|---------------  |------------------|----------------------------- |
| Green           | (0, 180, 0)      | Standby — all clear          |
| Yellow          |   (180, 100, 0)  | Warning — smoke detected     |
| Red             | (255, 0, 0)      | Danger —   fire confirmed    |
| 3× Green flash  | —                | Reset — fire suppressed      |
| Off             | (0, 0, 0)        | Boot initialisation |

---

## 4. System States

```
               ┌─────────────────────────────────────────────────────┐
               │                    STANDBY                          │
               │  Servo 1: sweeping 0°↔180°   LED: green             │
               │  Servo 2: parked at 90°       Pump: OFF             │
               │  DHT11: logging every 5s      Buzzer: silent        │
               └────────────┬──────────────────────┬──────────────── ┘
                            │ smoke detected       │ fire detected
                            ▼                      ▼ (×3 consecutive)
               ┌────────────────────────┐  ┌──────────────────────────┐
               │       WARNING          │  │    VERIFY  (internal)    │
               │  LED: yellow           │  │  5 more reads × 100ms    │
               │  Buzzer: 700Hz slow    │  │  All must be HIGH        │
               │  Servo 1: still sweeps │  └──────────┬───────────────┘
               │  Servo 2: parked       │             │ verified      │ false positive
               │  Pump: OFF             │             ▼               ▼
               └────────────┬───────────┘  ┌──────────────┐     back to STANDBY
                            │ smoke clears │    DANGER    │     |
                            ▼              │  LED: red    │     |
                        STANDBY            │  Buzzer: 1500Hz continuous │
                                           │  Servo 1: locked at heading│
                                           │  Servo 2: sweeping 0°↔180°│
                                           │  Pump: ON                  │
                                           └──────────┬─────────────────┘
                                                      │ fire sensor clears
                                                      ▼
                                               ┌────────────┐
                                               │   RESET    │
                                               │ Pump OFF   │
                                               │ Servo 2→90°│
                                               │ Servo 1→90°│
                                               │ 3× green   │
                                               │ flash      │
                                               └─────┬──────┘
                                                     ▼
                                                 STANDBY
```

---

## 5. How the Devices Coordinate

The system is structured as a **priority state machine** inside the main loop. Each iteration checks sensors in this order: fire counter → fire verification → smoke → standby. Higher-priority states override lower ones.

### Normal operation (Standby)
Servo 1 sweeps continuously. The DHT11 logs on a 5-second non-blocking timer. The flame and smoke sensors are polled every tick. The `confirm` counter resets to 0 on any non-fire read, preventing slow accumulation from random noise.

### Escalation to Warning
If the smoke sensor reads HIGH, the loop enters the WARNING branch. The servo 1 sweep logic is duplicated here (identical to standby) to ensure scanning continues. The buzzer fires a short 100ms beep every 800ms using another `ticks_diff` timer — this avoids using `time.sleep()` which would block servo movement. Servo 2 and the pump are untouched.

### Escalation to Danger
When `confirm` reaches 3, the system **pauses the main loop** and enters fire verification (see Section 6). If verified, it locks servo 1, turns on the red LED and continuous buzzer, calls `pump_on()`, then enters `spray_sweep()`.

`spray_sweep()` is a **blocking loop** — it does not return until the fire sensor reads clear. This is intentional: while fire is present, suppression is the only priority. Servo 2 steps 2° at a time with 40ms delay, checking the fire sensor at the end of each full pass (at 0° and 180°). Once the sensor clears, the function returns.

### Reset sequence
After `spray_sweep()` returns: pump off → buzzer off → 3 green LED flashes → servo 2 parks at 90° → servo 1 returns to 90° → all state variables reset → standby resumes.

### Coordination summary

| Device        | Standby                 | Warning                 | Danger          | Reset             |
|---------------|-------------------------|-------------------------|-----------------|-----------------  |
| Servo 1       | Sweeping at 2° per tick | Sweeping at 2° per tick | Locked          | Returns to 90°    |
| Servo 2       | Parked 90°              | Parked 90°              | Sweeping at 2° per tick with 40ms delay | Parks 90° |
| Pump          | OFF                     | OFF                     | ON continuously | OFF               |
| Buzzer        | Silent                  | 700Hz pulse every 800ms | 1500Hz continuously | Silent after pump off|
| LED           | Green                   | Yellow                  | Red             | 3× green flash |
| DHT11         | Logging every 5s       | Logging every 5s         | Not polled (blocked) | Resumes |

---

## 6. False-Positive Protection

The system uses a **two-stage confirmation gate** before the pump activates. This is the most safety-critical part of the logic.

**Stage 1 — Consecutive count:** The `confirm` variable increments on each fire sensor HIGH read and resets to 0 on any LOW read. The pump sequence does not begin until `confirm >= CONFIRM_COUNT` (default: 3). A single false read immediately resets the counter.

**Stage 2 — Verification:** Once Stage 1 is satisfied, `fire_verified()` is called. It takes `VERIFY_COUNT` (default: 5) additional readings, each 100ms apart. **Every single one must be HIGH.** If any read returns LOW, the function returns `False`, the counter resets, and the pump stays off. A message is printed: `False positive detected — pump stays OFF.`

Only when both stages pass does `pump_on()` execute. The pump activation line appears exactly once in the entire codebase.

Total minimum time from first detection to pump activation:
```
3 reads × (loop tick ~20ms) + 5 reads × 100ms = ~560ms minimum
```

---

## 7. File Structure

```
fire-suppression-esp32/
│
├── main.py                          # Full system — flash this to run
│
└── tests/
    ├── test_servo1_scanner.py       # Servo 1 sweep test (GPIO26)
    ├── test_servo2_nozzle.py        # Servo 2 spray sweep test (GPIO23)
    ├── test_fire_sensor.py          # Fire sensor live monitor (GPIO14)
    ├── test_smoke_sensor.py         # Smoke sensor live monitor (GPIO27)
    ├── test_relay_pump.py           # Relay ON/OFF cycles (GPIO5)
    ├── test_buzzer.py               # Buzzer frequency and pattern test (GPIO21)
    ├── test_dht11.py                # DHT11 repeated read test (GPIO13)
    ├── test_rgb_led.py              # RGB LED colour test (GPIO25/33/12)
    └── test_integration.py          # All devices — no pump activation
```

---

## 8. Running the Tests

Test each device individually before running `main.py`. The recommended order follows the dependency chain — verify output devices first, then sensors.

**Recommended order:**

1. `test_rgb_led.py` — confirm visual feedback works first
2. `test_buzzer.py` — confirm audio alerts work
3. `test_servo1_scanner.py` — confirm scanner servo
4. `test_servo2_nozzle.py` — confirm nozzle servo
5. `test_dht11.py` — confirm environmental sensor
6. `test_fire_sensor.py` — confirm flame detection (use a lighter ~20cm away)
7. `test_smoke_sensor.py` — confirm smoke detection (use cigarette smoke or alcohol spray)
8. `test_relay_pump.py` — confirm relay clicks (**disconnect pump load first**)
9. `test_integration.py` — run all devices together, no pump

Flash any test file to `main.py` on the board, or use a tool like **mpremote** or **Thonny** to run it directly:

```bash
# Using mpremote
mpremote connect /dev/ttyUSB0 run tests/test_rgb_led.py

# Or copy to board as main.py
mpremote connect /dev/ttyUSB0 cp tests/test_fire_sensor.py :main.py
```

---

## 9. Flashing to ESP32

### Prerequisites
```bash
pip install esptool mpremote
```

### Flash MicroPython firmware (first time only)
Download the latest MicroPython ESP32 `.bin` from https://micropython.org/download/ESP32_GENERIC/

```bash
# Erase flash
esptool.py --chip esp32 --port /dev/ttyUSB0 erase_flash

# Flash MicroPython
esptool.py --chip esp32 --port /dev/ttyUSB0 --baud 460800 \
  write_flash -z 0x1000 ESP32_GENERIC-20241129-v1.24.1.bin
```

### Upload and run main system
```bash
mpremote connect /dev/ttyUSB0 cp main.py :main.py
mpremote connect /dev/ttyUSB0 reset
```

### Monitor serial output
```bash
mpremote connect /dev/ttyUSB0
# or
screen /dev/ttyUSB0 115200
```

---

## 10. Tuning Parameters

All tuning constants are at the top of `main.py` under the `TUNING` block.

| Parameter           | Default | Effect                                                         |
|---------------------|---------|----------------------------------------------------------------|
| `RELAY_ACTIVE_LOW`  | `False` | Set `True` if relay triggers on LOW signal                     |
| `SERVO_MIN_US`      | `500`   | Pulse width for 0° — adjust if servo doesn't reach full range  |
| `SERVO_MAX_US`      | `2400`  | Pulse width for 180° — adjust if servo overshoots              |
| `SCAN_STEP`         | `2`     | Degrees per tick for servo 1 — smaller = smoother, slower      |
| `SCAN_DELAY_MS`     | `20`    | Delay per tick for servo 1 — increase to slow the scan         |
| `SPRAY_STEP`        | `2`     | Degrees per tick for servo 2                                   |
| `SPRAY_DELAY_MS`    | `40`    | Delay per tick for servo 2 — increase for more water per angle |
| `CONFIRM_COUNT`     | `3`     | Consecutive fire reads before entering verification            |
| `VERIFY_COUNT`      | `5`     | Reads during verification phase — all must be HIGH             |
| `VERIFY_DELAY_MS`   | `100`   | Interval between verification reads                            |
| `DHT_INTERVAL_MS`   | `5000`  | How often DHT11 is sampled                                     |

**Recommended adjustments by environment:**

- **High ambient IR** (direct sunlight, incandescent bulbs): Increase `CONFIRM_COUNT` to 5 and `VERIFY_COUNT` to 8.
- **Fast-response requirement**: Decrease `CONFIRM_COUNT` to 2 — accept slightly higher false-positive risk.
- **Large coverage area**: Decrease `SCAN_STEP` to 1 and increase `SCAN_DELAY_MS` to ensure sensor settles at each position.
- **Slow pump or low water pressure**: Increase `SPRAY_DELAY_MS` to 60–80ms to compensate.

---

## Licence

MIT — free to use, modify, and redistribute with attribution.
