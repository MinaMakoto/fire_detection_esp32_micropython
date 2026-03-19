# ============================================================
# TEST: Relay Module / Pump (GPIO5)
# Board: Plain ESP32 | MicroPython
# ============================================================
# What this tests:
#   - Relay switching via GPIO5
#   - Both ACTIVE_HIGH and ACTIVE_LOW wiring modes
#   - ON/OFF cycle with audible click confirmation
#   - Safe startup (relay OFF before any test begins)
#
# Pass criteria:
#   - Audible click when relay energises (ON)
#   - Audible click when relay de-energises (OFF)
#   - Pump/load activates and deactivates in sync with relay LED
#   - No relay activation at startup
#
# Wiring:
#   IN  → GPIO5   (control signal)
#   VCC → 5V      (relay coil power — use external 5V if possible)
#   GND → GND     (shared with ESP32)
#
#   Pump connections (on relay terminal block):
#   COM → positive supply rail for pump
#   NO  → pump positive terminal  (Normally Open — use this)
#   NC  → not used
#
# RELAY_ACTIVE_LOW setting:
#   False → GPIO HIGH energises relay  (most modules with optocoupler)
#   True  → GPIO LOW  energises relay  (some modules marked "LOW trigger")
#   Check your module's label or try both.
#
# SAFETY: Disconnect pump/load during initial wiring test.
# Confirm relay clicks correctly before connecting water pump.
# ============================================================

import machine
import time

# ---- Config ----
RELAY_PIN        = 5
RELAY_ACTIVE_LOW = False   # Change to True if relay triggers on LOW

# ---- Init — safe state first ----
relay = machine.Pin(RELAY_PIN, machine.Pin.OUT)

def pump_on():
    relay.value(0 if RELAY_ACTIVE_LOW else 1)

def pump_off():
    relay.value(1 if RELAY_ACTIVE_LOW else 0)

# Guarantee OFF before anything else
pump_off()

# ---- Test sequence ----
print("=" * 40)
print("Relay / Pump — GPIO5 Test")
print(f"Mode: {'ACTIVE LOW' if RELAY_ACTIVE_LOW else 'ACTIVE HIGH'}")
print("=" * 40)
print("Relay starts in OFF state.\n")

time.sleep(1)

# 3 ON/OFF cycles with delays
for i in range(1, 4):
    print(f"[Cycle {i}/3] Relay ON  — pump should activate...")
    pump_on()
    time.sleep(2)

    print(f"[Cycle {i}/3] Relay OFF — pump should stop.")
    pump_off()
    time.sleep(1)
    print()

# Final safe state
pump_off()
print("✓ Relay test complete. Relay is OFF.")
print()
print("If relay did NOT click:")
print("  1. Swap RELAY_ACTIVE_LOW to True and re-run")
print("  2. Check VCC — relay coil needs 5V")
print("  3. Verify GPIO5 is not used by another peripheral at boot")
print()
print("If relay clicked but pump didn't run:")
print("  1. Confirm pump is wired to COM + NO terminals (not NC)")
print("  2. Check pump supply voltage")
