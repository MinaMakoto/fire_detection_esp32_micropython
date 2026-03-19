# ============================================================
# TEST: Servo 1 — Scanner Servo (GPIO26)
# Board: Plain ESP32 | MicroPython
# ============================================================
# What this tests:
#   - PWM signal generation at 50 Hz on GPIO26
#   - Pulse width mapping: 500µs (0°) → 2400µs (180°)
#   - Full 0°→180°→0° sweep cycle
#   - Centre park at 90°
#
# Pass criteria:
#   - Servo physically sweeps smoothly from 0° to 180° and back
#   - No jitter or missed steps
#   - Returns cleanly to 90° at end
#
# Wiring:
#   Signal (orange/yellow) → GPIO26
#   VCC (red)              → 5V (external supply recommended)
#   GND (brown/black)      → GND (shared with ESP32)
# ============================================================

import machine
import time

# ---- Config ----
SERVO1_PIN   = 26
SERVO_FREQ   = 50       # Hz — standard for hobby servos
SERVO_MIN_US = 500      # pulse width at 0°
SERVO_MAX_US = 2400     # pulse width at 180°
STEP_DEG     = 2        # degrees per tick
STEP_DELAY   = 20       # ms between ticks

# ---- Init ----
servo1 = machine.PWM(machine.Pin(SERVO1_PIN), freq=SERVO_FREQ)

def angle_to_duty(angle):
    """Convert angle (0-180) to ESP32 PWM duty (0-1023)."""
    pulse_us = SERVO_MIN_US + (angle / 180.0) * (SERVO_MAX_US - SERVO_MIN_US)
    return int(pulse_us / 20000.0 * 1023)

def set_angle(angle):
    angle = max(0, min(180, angle))
    servo1.duty(angle_to_duty(angle))

# ---- Test sequence ----
print("=" * 40)
print("Servo 1 (Scanner) — GPIO26 Test")
print("=" * 40)

# Step 1: Centre
print("\n[1] Centering at 90°...")
set_angle(90)
time.sleep(1)

# Step 2: Sweep to 0°
print("[2] Sweeping to 0°...")
for a in range(90, -1, -STEP_DEG):
    set_angle(a)
    time.sleep_ms(STEP_DELAY)
print("    At 0°")
time.sleep(500)

# Step 3: Sweep to 180°
print("[3] Sweeping to 180°...")
for a in range(0, 181, STEP_DEG):
    set_angle(a)
    time.sleep_ms(STEP_DELAY)
print("    At 180°")
time.sleep(500)

# Step 4: Sweep back to 0°
print("[4] Sweeping back to 0°...")
for a in range(180, -1, -STEP_DEG):
    set_angle(a)
    time.sleep_ms(STEP_DELAY)
print("    At 0°")
time.sleep(500)

# Step 5: Return to centre
print("[5] Returning to 90° (park position)...")
for a in range(0, 91, STEP_DEG):
    set_angle(a)
    time.sleep_ms(STEP_DELAY)

time.sleep(1)
servo1.deinit()  # Release PWM — prevents servo buzz at rest

print("\n✓ Servo 1 test complete.")
print("  Expected: smooth sweep 0→180→0, parked at 90°.")
print("  If jitter occurs: check VCC — use external 5V supply.")
