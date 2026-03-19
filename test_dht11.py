# ============================================================
# TEST: DHT11 Temperature & Humidity Sensor (GPIO13)
# Board: Plain ESP32 | MicroPython
# ============================================================
# What this tests:
#   - One-wire communication with DHT11 on GPIO13
#   - Temperature read in °C
#   - Relative humidity read in %RH
#   - Error handling for OSError (sensor absent or wiring fault)
#   - Non-blocking polling pattern used in main system
#     (reads every 5000ms, not continuously)
#
# Pass criteria:
#   - Temperature reads between 10°C–50°C for room conditions
#   - Humidity reads between 20%–90% for typical indoor air
#   - No OSError on repeated reads
#   - Second read slightly different from first (sensor live)
#
# Wiring:
#   VCC → 3.3V
#   GND → GND
#   DATA → GPIO13 + 10kΩ pull-up resistor to 3.3V
#
# DHT11 limitations:
#   - Resolution: 1°C / 1% RH (no decimals)
#   - Range: 0–50°C, 20–90% RH
#   - Minimum sample interval: 1 second between reads
#   - Accuracy: ±2°C, ±5% RH
#
# DHT22 drop-in compatibility:
#   Change dht.DHT11 → dht.DHT22 for higher accuracy (0.5°C / 2–5% RH)
#   Same wiring applies.
# ============================================================

import machine
import dht
import time

# ---- Config ----
DHT_PIN      = 13
READ_COUNT   = 10        # number of test reads
READ_DELAY_S = 2         # seconds between reads (DHT11 min = 1s)

# ---- Init ----
sensor = dht.DHT11(machine.Pin(DHT_PIN))

# ---- Test ----
print("=" * 40)
print("DHT11 — GPIO13 Test")
print(f"Taking {READ_COUNT} readings every {READ_DELAY_S}s")
print("=" * 40)

success = 0
errors  = 0

for i in range(1, READ_COUNT + 1):
    try:
        sensor.measure()
        temp = sensor.temperature()
        hum  = sensor.humidity()
        print(f"[{i:02d}] Temperature: {temp}°C   Humidity: {hum}% RH")
        success += 1
    except OSError as e:
        print(f"[{i:02d}] ERROR: {e}")
        errors += 1

    time.sleep(READ_DELAY_S)

print()
print(f"✓ Test complete: {success}/{READ_COUNT} successful reads, {errors} errors.")

if errors == 0:
    print("  Sensor is working correctly.")
elif errors < READ_COUNT // 2:
    print("  Occasional errors — check pull-up resistor (10kΩ, DATA→3.3V).")
else:
    print("  Majority of reads failed:")
    print("  - Check wiring: VCC=3.3V, correct GPIO, pull-up resistor")
    print("  - Confirm DHT11 (not DHT22) — change dht.DHT11→dht.DHT22 if needed")
    print("  - Try increasing READ_DELAY_S to 3")
