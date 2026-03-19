# ============================================================
# TEST: Smoke Sensor (GPIO27)
# Board: Plain ESP32 | MicroPython
# ============================================================
# What this tests:
#   - Digital read on GPIO27
#   - Active-HIGH logic (D0 HIGH = smoke/gas above threshold)
#   - Continuous monitoring with clean state-change output
#   - WARNING state behaviour — no pump, no servo 2 activation
#
# Pass criteria:
#   - "CLEAR" when air is clean
#   - "SMOKE/GAS DETECTED" when threshold exceeded
#   - State changes printed immediately
#   - No false triggers during normal idle
#
# Wiring:
#   VCC → 5V  (MQ-series sensors need 5V for heater element)
#   GND → GND
#   D0  → GPIO27
#   A0  → not connected in this test
#
# Sensor notes:
#   - MQ-2 detects LPG, smoke, alcohol, propane, hydrogen, methane
#   - Requires ~20s warm-up time after power-on for stable readings
#   - Sensitivity set via onboard potentiometer (turn CW = more sensitive)
#   - D0 goes HIGH when gas concentration exceeds threshold
#
# To trigger: briefly expose sensor to cigarette smoke, lighter gas,
# or alcohol spray. Do NOT use open flame — that tests the fire sensor.
#
# IMPORTANT: If sensor always reads HIGH on first boot, wait 20–30s
# for the heating element to stabilise before testing.
# ============================================================

import machine
import time

# ---- Config ----
SMOKE_PIN = 27
POLL_MS   = 150

# ---- Init ----
smoke_pin = machine.Pin(SMOKE_PIN, machine.Pin.IN)

def smoke_detected():
    return smoke_pin.value() == 1   # HIGH = smoke above threshold

# ---- Warm-up notice ----
print("=" * 40)
print("Smoke Sensor — GPIO27 Test")
print("=" * 40)
print("NOTE: Allow 20–30s warm-up after power-on.")
print("Monitoring... (Ctrl+C to stop)\n")

last_state = None
event_count = 0

try:
    while True:
        reading = smoke_detected()

        if reading != last_state:
            event_count += 1
            if reading:
                print(f"[{event_count}] >>> SMOKE/GAS DETECTED  (D0=HIGH, GPIO27={smoke_pin.value()})")
                print("        In main system: LED → yellow, slow beep, servo 1 keeps sweeping.")
                print("        Pump and servo 2 remain OFF.")
            else:
                print(f"[{event_count}]     Clear               (D0=LOW,  GPIO27={smoke_pin.value()})")
                print("        In main system: LED → green, buzzer off.")
            last_state = reading

        time.sleep_ms(POLL_MS)

except KeyboardInterrupt:
    print("\nTest stopped.")
    print(f"Total state changes observed: {event_count}")
    print(f"Final state: {'SMOKE' if smoke_detected() else 'CLEAR'}")
