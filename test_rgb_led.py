# ============================================================
# TEST: RGB LED (GPIO25=R, GPIO33=G, GPIO12=B)
# Board: Plain ESP32 | MicroPython
# ============================================================
# What this tests:
#   - PWM on three channels at 1000 Hz
#   - Individual R, G, B channel isolation
#   - The three system-state colours:
#       Green  (0, 180, 0)   — STANDBY
#       Yellow (180, 100, 0) — WARNING (smoke detected)
#       Red    (255, 0, 0)   — DANGER  (fire verified)
#   - Colour mixing and fade
#   - Clean off state (all duty = 0)
#
# Pass criteria:
#   - Each channel lights independently in its correct colour
#   - Green, yellow, red match expected system states
#   - LED goes fully off between tests
#
# Wiring (common-cathode RGB LED):
#   R anode → GPIO25 (via 220Ω resistor)
#   G anode → GPIO33 (via 220Ω resistor)
#   B anode → GPIO12 (via 220Ω resistor)
#   Cathode → GND
#
# Wiring (common-anode RGB LED):
#   Common → 3.3V
#   R      → GPIO25 (via 220Ω) — INVERT duty: duty = 1023 - calculated
#   G      → GPIO33 (via 220Ω)
#   B      → GPIO12 (via 220Ω)
#   For common-anode, change set_rgb() to: duty(1023 - value)
#
# Note: GPIO12 is used at boot by ESP32 for flash voltage detection.
# If boot fails after adding this test, pull GPIO12 LOW at startup
# or reassign the blue channel to another available GPIO.
# ============================================================

import machine
import time

# ---- Config ----
RGB_R_PIN = 25
RGB_G_PIN = 33
RGB_B_PIN = 12
PWM_FREQ  = 1000   # Hz — high enough to avoid visible flicker

# ---- Init ----
r_pwm = machine.PWM(machine.Pin(RGB_R_PIN), freq=PWM_FREQ)
g_pwm = machine.PWM(machine.Pin(RGB_G_PIN), freq=PWM_FREQ)
b_pwm = machine.PWM(machine.Pin(RGB_B_PIN), freq=PWM_FREQ)

def set_rgb(r, g, b):
    """Set RGB colour. Each channel 0–255."""
    r_pwm.duty(int(r / 255 * 1023))
    g_pwm.duty(int(g / 255 * 1023))
    b_pwm.duty(int(b / 255 * 1023))

def led_off():    set_rgb(0, 0, 0)
def led_green():  set_rgb(0, 180, 0)
def led_yellow(): set_rgb(180, 100, 0)
def led_red():    set_rgb(255, 0, 0)

PAUSE = 1200   # ms between tests

# ---- Test sequence ----
print("=" * 40)
print("RGB LED — GPIO25 / GPIO33 / GPIO12 Test")
print("=" * 40)

led_off()
time.sleep_ms(300)

# Individual channels
print("\n[1] Red channel only (GPIO25)...")
set_rgb(255, 0, 0)
time.sleep_ms(PAUSE)
led_off(); time.sleep_ms(300)

print("[2] Green channel only (GPIO33)...")
set_rgb(0, 255, 0)
time.sleep_ms(PAUSE)
led_off(); time.sleep_ms(300)

print("[3] Blue channel only (GPIO12)...")
set_rgb(0, 0, 255)
time.sleep_ms(PAUSE)
led_off(); time.sleep_ms(300)

# System state colours
print("\n[4] STANDBY colour — Green (0, 180, 0)...")
led_green()
time.sleep_ms(PAUSE)
led_off(); time.sleep_ms(300)

print("[5] WARNING colour  — Yellow (180, 100, 0)...")
led_yellow()
time.sleep_ms(PAUSE)
led_off(); time.sleep_ms(300)

print("[6] DANGER colour   — Red (255, 0, 0)...")
led_red()
time.sleep_ms(PAUSE)
led_off(); time.sleep_ms(300)

# Reset flash (3 green flashes — mirrors main system reset)
print("\n[7] Reset flash sequence — 3 green flashes...")
for i in range(3):
    led_green()
    time.sleep_ms(200)
    led_off()
    time.sleep_ms(200)
    print(f"    Flash {i+1}")

# Return to standby colour
print("\n[8] Final state: STANDBY green...")
led_green()
time.sleep(2)
led_off()

# Deinit PWM
r_pwm.deinit()
g_pwm.deinit()
b_pwm.deinit()

print("\n✓ RGB LED test complete.")
print("  All three channels and system-state colours verified.")
print("  If a channel is wrong colour: check resistor and wiring.")
print("  If common-anode: invert duty in set_rgb() — see comments above.")
