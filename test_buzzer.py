# ============================================================
# TEST: Buzzer (GPIO21)
# Board: Plain ESP32 | MicroPython
# ============================================================
# What this tests:
#   - PWM-driven active buzzer on GPIO21
#   - Two frequencies used in the main system:
#       700 Hz  — WARNING (smoke detected, slow beep)
#       1500 Hz — DANGER  (fire confirmed, continuous tone)
#   - duty(512) = 50% duty cycle = maximum volume
#   - duty(0)   = silent
#
# Pass criteria:
#   - Audible lower-pitched beep at 700 Hz
#   - Audible higher-pitched continuous tone at 1500 Hz
#   - Clean silence between tests (no residual buzz)
#
# Wiring (passive buzzer):
#   Positive (+) → GPIO21
#   Negative (−) → GND
#
# Wiring (active buzzer):
#   VCC → GPIO21 (or 3.3V with transistor driver)
#   GND → GND
#   Active buzzers have a built-in oscillator — frequency control
#   via PWM may not work; use duty(512)/duty(0) only.
#
# Note: If volume is low, add a 100Ω series resistor or a
# transistor driver (BC547, 2N2222) between GPIO and buzzer.
# ============================================================

import machine
import time

# ---- Config ----
BUZZER_PIN = 21

# ---- Init ----
buzzer = machine.PWM(machine.Pin(BUZZER_PIN))
buzzer.duty(0)   # Silent at startup

def buzzer_on(freq=1500):
    buzzer.freq(freq)
    buzzer.duty(512)   # 50% duty — maximum loudness

def buzzer_off():
    buzzer.duty(0)

# ---- Test sequence ----
print("=" * 40)
print("Buzzer — GPIO21 Test")
print("=" * 40)

# Test 1: WARNING beep pattern (smoke state in main system)
print("\n[1] WARNING pattern — 700 Hz slow beep (3 beeps)...")
for i in range(3):
    buzzer_on(700)
    time.sleep_ms(200)
    buzzer_off()
    time.sleep_ms(700)
    print(f"    Beep {i+1}")

time.sleep(500)

# Test 2: DANGER tone (fire confirmed state in main system)
print("\n[2] DANGER tone — 1500 Hz continuous (2 seconds)...")
buzzer_on(1500)
time.sleep(2)
buzzer_off()
print("    Tone ended.")

time.sleep(500)

# Test 3: Frequency sweep — confirms PWM frequency control works
print("\n[3] Frequency sweep — 500 Hz to 2500 Hz...")
for freq in range(500, 2501, 100):
    buzzer.freq(freq)
    buzzer.duty(300)
    time.sleep_ms(30)
buzzer_off()
print("    Sweep complete.")

time.sleep(500)

# Test 4: Rapid beep (reset flash pattern — not in buzzer but
# included here to demonstrate short pulse control)
print("\n[4] Rapid pulse test (5 quick beeps)...")
for _ in range(5):
    buzzer_on(1200)
    time.sleep_ms(80)
    buzzer_off()
    time.sleep_ms(120)

buzzer_off()
buzzer.deinit()

print("\n✓ Buzzer test complete.")
print("  If no sound: check wiring polarity and buzzer type.")
print("  Active buzzers may not respond to frequency changes.")
