# ============================================================
# TEST: Servo 2 — Nozzle Servo (GPIO23)
# Board: Plain ESP32 | MicroPython
# ============================================================
# What this tests:
#   - PWM signal on GPIO23 at 50 Hz
#   - Slower sweep speed (SPRAY_DELAY_MS = 40ms) — matches
#     main system behaviour where slower = more water per angle
#   - Full 0°→180°→0° spray sweep pattern (2 full passes)
#   - Park at 90° on completion
#
# Pass criteria:
#   - Servo sweeps noticeably slower than servo 1
#   - Reaches both 0° and 180° endpoints cleanly
#   - Parks at 90° without jitter
#
# Wiring:
#   Signal (orange/yellow) → GPIO23
#   VCC (red)              → 5V (external supply recommended)
#   GND (brown/black)      → GND (shared with ESP32)
#
# NOTE: In the main system servo 2 is LOCKED OFF until fire is
# verified. This test bypasses that gate intentionally.
# ============================================================

import machine
import time

# ---- Config ----
SERVO2_PIN   = 23
SERVO_FREQ   = 50
SERVO_MIN_US = 500
SERVO_MAX_US = 2400
SPRAY_STEP   = 2        # degrees per tick — same as main system
SPRAY_DELAY  = 40       # ms per tick — deliberately slower than servo 1

# ---- Init ----
servo2 = machine.PWM(machine.Pin(SERVO2_PIN), freq=SERVO_FREQ)

def angle_to_duty(angle):
    pulse_us = SERVO_MIN_US + (angle / 180.0) * (SERVO_MAX_US - SERVO_MIN_US)
    return int(pulse_us / 20000.0 * 1023)

def set_angle(angle):
    angle = max(0, min(180, angle))
    servo2.duty(angle_to_duty(angle))

def spray_pass(start, end, label):
    step = SPRAY_STEP if end > start else -SPRAY_STEP
    for a in range(start, end + step, step):
        a = max(0, min(180, a))
        set_angle(a)
        time.sleep_ms(SPRAY_DELAY)
    print(f"    {label} — at {end}°")

# ---- Test sequence ----
print("=" * 40)
print("Servo 2 (Nozzle) — GPIO23 Test")
print("=" * 40)

# Step 1: Park at 90°
print("\n[1] Parking at 90°...")
set_angle(90)
time.sleep(1)

# Step 2: Move to 0° start position (mirrors main system)
print("[2] Moving to 0° start (spray ready)...")
set_angle(0)
time.sleep_ms(700)

# Step 3: Two full spray sweep passes
print("[3] Spray sweep — Pass 1 (0°→180°)...")
spray_pass(0, 180, "Pass 1 complete")
time.sleep_ms(200)

print("[4] Spray sweep — Pass 2 (180°→0°)...")
spray_pass(180, 0, "Pass 2 complete")
time.sleep_ms(200)

# Step 4: Return to park
print("[5] Returning to park position (90°)...")
spray_pass(0, 90, "Parked at 90°")

time.sleep(1)
servo2.deinit()

print("\n✓ Servo 2 test complete.")
print("  Expected: slow deliberate sweep — ~7.2s per 180° pass.")
print("  Speed difference from servo 1 is intentional (water coverage).")
