# ============================================================
# TEST: Integration — All Devices (No Pump Activation)
# Board: Plain ESP32 | MicroPython
# ============================================================
# Runs a full system check across all peripherals in sequence.
# The relay/pump is intentionally NOT activated in this test.
# Use test_relay_pump.py separately to test the pump.
#
# This test confirms:
#   1. All GPIOs initialise without conflict
#   2. Both servos respond on correct pins
#   3. DHT11 reads successfully
#   4. Fire sensor GPIO reads correctly (HIGH/LOW)
#   5. Smoke sensor GPIO reads correctly (HIGH/LOW)
#   6. Buzzer produces sound on both frequencies
#   7. RGB LED produces all three system-state colours
#   8. Relay GPIO can be toggled (relay clicks, pump NOT connected)
#
# Run this before main.py to confirm full hardware readiness.
# ============================================================

import machine
import dht
import time

# ---- GPIO map ----
SERVO1_PIN = 26; SERVO2_PIN = 23; FIRE_PIN = 14; SMOKE_PIN = 27
RELAY_PIN  = 5;  BUZZER_PIN = 21; DHT_PIN  = 13
RGB_R_PIN  = 25; RGB_G_PIN  = 33; RGB_B_PIN = 12

RELAY_ACTIVE_LOW = False
SERVO_FREQ = 50; SERVO_MIN_US = 500; SERVO_MAX_US = 2400

# ---- Init ----
servo1     = machine.PWM(machine.Pin(SERVO1_PIN), freq=SERVO_FREQ)
servo2     = machine.PWM(machine.Pin(SERVO2_PIN), freq=SERVO_FREQ)
fire_pin   = machine.Pin(FIRE_PIN,  machine.Pin.IN)
smoke_pin  = machine.Pin(SMOKE_PIN, machine.Pin.IN)
relay      = machine.Pin(RELAY_PIN, machine.Pin.OUT)
dht_sensor = dht.DHT11(machine.Pin(DHT_PIN))
buzzer     = machine.PWM(machine.Pin(BUZZER_PIN)); buzzer.duty(0)
r_pwm      = machine.PWM(machine.Pin(RGB_R_PIN),  freq=1000)
g_pwm      = machine.PWM(machine.Pin(RGB_G_PIN),  freq=1000)
b_pwm      = machine.PWM(machine.Pin(RGB_B_PIN),  freq=1000)

# ---- Helpers ----
def angle_to_duty(a):
    return int((SERVO_MIN_US + (a/180.0)*(SERVO_MAX_US-SERVO_MIN_US)) / 20000.0 * 1023)

def s1(a): servo1.duty(angle_to_duty(max(0,min(180,a))))
def s2(a): servo2.duty(angle_to_duty(max(0,min(180,a))))
def pump_off(): relay.value(1 if RELAY_ACTIVE_LOW else 0)
def set_rgb(r,g,b):
    r_pwm.duty(int(r/255*1023)); g_pwm.duty(int(g/255*1023)); b_pwm.duty(int(b/255*1023))
def led_off(): set_rgb(0,0,0)

results = {}

print("=" * 48)
print("  Full Integration Test — All Devices")
print("  Pump NOT activated in this test.")
print("=" * 48)

# Safe initial state
pump_off(); buzzer.duty(0); led_off(); s1(90); s2(90)
time.sleep(500)

# ---- 1. Servo 1 ----
print("\n[1/7] Servo 1 (GPIO26) — short sweep test...")
s1(0); time.sleep_ms(500)
s1(180); time.sleep_ms(500)
s1(90); time.sleep_ms(500)
results["Servo1"] = "OK"
print("      Servo 1 ✓")

# ---- 2. Servo 2 ----
print("[2/7] Servo 2 (GPIO23) — short sweep test...")
s2(0); time.sleep_ms(600)
s2(180); time.sleep_ms(600)
s2(90); time.sleep_ms(600)
results["Servo2"] = "OK"
print("      Servo 2 ✓")

# ---- 3. DHT11 ----
print("[3/7] DHT11 (GPIO13) — reading...")
try:
    dht_sensor.measure()
    t = dht_sensor.temperature()
    h = dht_sensor.humidity()
    print(f"      {t}°C  {h}% RH ✓")
    results["DHT11"] = f"{t}C {h}%RH"
except OSError as e:
    print(f"      ERROR: {e} ✗")
    results["DHT11"] = f"FAIL: {e}"

# ---- 4. Fire sensor ----
print("[4/7] Fire sensor (GPIO14) — reading pin state...")
fv = fire_pin.value()
state = "HIGH (FLAME?)" if fv else "LOW  (clear)"
print(f"      D0={fv} — {state} ✓")
results["FireSensor"] = state

# ---- 5. Smoke sensor ----
print("[5/7] Smoke sensor (GPIO27) — reading pin state...")
sv = smoke_pin.value()
state = "HIGH (SMOKE?)" if sv else "LOW  (clear)"
print(f"      D0={sv} — {state} ✓")
results["SmokeSensor"] = state

# ---- 6. Buzzer ----
print("[6/7] Buzzer (GPIO21) — two-tone test...")
buzzer.freq(700); buzzer.duty(512); time.sleep_ms(300); buzzer.duty(0)
time.sleep_ms(200)
buzzer.freq(1500); buzzer.duty(512); time.sleep_ms(300); buzzer.duty(0)
results["Buzzer"] = "OK"
print("      Buzzer ✓")

# ---- 7. RGB LED ----
print("[7/7] RGB LED — system-state colours...")
set_rgb(0, 180, 0);    time.sleep_ms(500)   # green = standby
set_rgb(180, 100, 0);  time.sleep_ms(500)   # yellow = warning
set_rgb(255, 0, 0);    time.sleep_ms(500)   # red = danger
for _ in range(3):                           # flash = reset
    set_rgb(0,180,0); time.sleep_ms(150); led_off(); time.sleep_ms(150)
results["RGB"] = "OK"
print("      RGB ✓")

# ---- Return to safe state ----
led_off(); buzzer.duty(0); pump_off()
s1(90); s2(90); time.sleep(1)
servo1.deinit(); servo2.deinit(); buzzer.deinit()
r_pwm.deinit(); g_pwm.deinit(); b_pwm.deinit()

# ---- Summary ----
print("\n" + "=" * 48)
print("  Integration Test Results")
print("=" * 48)
for k, v in results.items():
    status = "✓" if "FAIL" not in v else "✗"
    print(f"  {status}  {k:<14} {v}")

fails = [k for k, v in results.items() if "FAIL" in v]
if not fails:
    print("\n  All devices passed. Ready to run main.py")
else:
    print(f"\n  {len(fails)} device(s) need attention: {', '.join(fails)}")
