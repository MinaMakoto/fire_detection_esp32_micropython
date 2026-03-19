# ============================================================
# TEST: Fire Sensor (GPIO14)
# Board: Plain ESP32 | MicroPython
# ============================================================
# What this tests:
#   - Digital read on GPIO14
#   - Correct active-HIGH logic (D0 HIGH = flame detected)
#   - Continuous polling with state-change reporting
#   - The CONFIRM_COUNT logic used in the main system
#     (3 consecutive HIGH reads before triggering)
#
# Pass criteria:
#   - "CLEAR" printed when no flame present
#   - "FLAME DETECTED" printed immediately when sensor triggers
#   - After 3 consecutive detections: "CONFIRM threshold reached"
#   - Returns to CLEAR when flame removed
#
# Wiring:
#   VCC → 3.3V
#   GND → GND
#   D0  → GPIO14   (digital output — used by main system)
#   A0  → not connected in this test
#
# Sensor notes:
#   - Detects IR wavelength ~760–1100 nm (candle, lighter, matches)
#   - Sensitivity adjustable via onboard potentiometer
#   - D0 is HIGH when flame is within range
#   - D0 is LOW when no flame — this is ACTIVE HIGH logic
#
# Hold a lighter or candle ~10–30 cm from the sensor to trigger.
# ============================================================

import machine
import time

# ---- Config ----
FIRE_PIN      = 14
CONFIRM_COUNT = 3       # consecutive reads required — same as main system
POLL_MS       = 100     # read interval

# ---- Init ----
fire_pin = machine.Pin(FIRE_PIN, machine.Pin.IN)

def fire_detected():
    return fire_pin.value() == 1   # HIGH = flame present

# ---- Live monitor ----
print("=" * 40)
print("Fire Sensor — GPIO14 Test")
print(f"Confirm threshold: {CONFIRM_COUNT} consecutive reads")
print("=" * 40)
print("Monitoring... (Ctrl+C to stop)\n")

confirm   = 0
last_state = None

try:
    while True:
        reading = fire_detected()

        if reading != last_state:
            if reading:
                print(f">>> FLAME DETECTED  (D0=HIGH, GPIO14={fire_pin.value()})")
            else:
                print(f"    Clear           (D0=LOW,  GPIO14={fire_pin.value()})")
            last_state = reading

        if reading:
            confirm += 1
            if confirm == CONFIRM_COUNT:
                print(f"!!! CONFIRM threshold reached ({CONFIRM_COUNT} consecutive reads)")
                print("    In main system: verification sequence would start now.")
        else:
            if confirm > 0:
                print(f"    Reset confirm counter (was {confirm})")
            confirm = 0

        time.sleep_ms(POLL_MS)

except KeyboardInterrupt:
    print("\nTest stopped.")
    print(f"Final state: {'FLAME' if fire_detected() else 'CLEAR'}")
