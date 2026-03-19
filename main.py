# ============================================================
# Full Fire Suppression System
# Board: Plain ESP32
# ============================================================
# GPIO pins:
#   Servo 1 (scanner) → GPIO26
#   Servo 2 (nozzle)  → GPIO23
#   Fire sensor       → GPIO14
#   Smoke sensor D0   → GPIO27
#   Relay / pump      → GPIO5
#   Buzzer            → GPIO21
#   DHT11             → GPIO13
#   RGB R             → GPIO25
#   RGB G             → GPIO33
#   RGB B             → GPIO12
#
# Behaviour:
#   STANDBY  — Servo 1 sweeps 0-180, LED green, DHT11 logs
#              Servo 2 OFF, pump OFF — strictly no exceptions
#
#   WARNING  — Smoke detected, LED yellow, slow beep
#              Servo 1 keeps sweeping
#              Servo 2 OFF, pump OFF — strictly no exceptions
#
#   DANGER   — Fire confirmed (3 reads) + verified (5 reads):
#              Servo 1 locks at detection angle
#              Servo 2 sweeps full 0°→180°→0° continuously
#              Pump ON — sprays at every angle
#              LED red, buzzer continuous
#              Continues until fire sensor clears
#
#   RESET    — Fire gone, pump OFF, servo 2 parks at 90°
#              Servo 1 resumes sweep, LED green flashes
# ============================================================

import machine
import dht
import time

# ================================================================
# GPIO CONFIG
# ================================================================

SERVO1_PIN      = 26
SERVO2_PIN      = 23
FIRE_PIN        = 14
SMOKE_PIN       = 27
RELAY_PIN       = 5
BUZZER_PIN      = 21
DHT_PIN         = 13
RGB_R_PIN       = 25
RGB_G_PIN       = 33
RGB_B_PIN       = 12

# ================================================================
# TUNING
# ================================================================

RELAY_ACTIVE_LOW = False   # LOW = pump ON (standard relay modules)

SERVO_FREQ      = 50      # Hz
SERVO_MIN_US    = 500     # pulse → 0°
SERVO_MAX_US    = 2400    # pulse → 180°

SCAN_STEP       = 2       # servo 1 degrees per tick
SCAN_DELAY_MS   = 20      # servo 1 ms per tick

SPRAY_STEP      = 2       # servo 2 degrees per tick
SPRAY_DELAY_MS  = 40      # servo 2 ms per tick (slower = more water per angle)

CONFIRM_COUNT   = 3       # consecutive fire reads to enter DANGER
VERIFY_COUNT    = 5       # additional reads to confirm before pump ON
VERIFY_DELAY_MS = 100     # ms between verification reads

DHT_INTERVAL_MS = 5000    # ms between DHT11 readings

# ================================================================
# HARDWARE INIT
# ================================================================

servo1     = machine.PWM(machine.Pin(SERVO1_PIN), freq=SERVO_FREQ)
servo2     = machine.PWM(machine.Pin(SERVO2_PIN), freq=SERVO_FREQ)
fire_pin   = machine.Pin(FIRE_PIN,  machine.Pin.IN)
smoke_pin  = machine.Pin(SMOKE_PIN, machine.Pin.IN)
relay      = machine.Pin(RELAY_PIN, machine.Pin.OUT)
dht_sensor = dht.DHT11(machine.Pin(DHT_PIN))

buzzer = machine.PWM(machine.Pin(BUZZER_PIN))
buzzer.duty(0)

r_pwm = machine.PWM(machine.Pin(RGB_R_PIN), freq=1000)
g_pwm = machine.PWM(machine.Pin(RGB_G_PIN), freq=1000)
b_pwm = machine.PWM(machine.Pin(RGB_B_PIN), freq=1000)

# ================================================================
# LOW-LEVEL HELPERS
# ================================================================

def angle_to_duty(angle):
    pulse_us = SERVO_MIN_US + (angle / 180.0) * (SERVO_MAX_US - SERVO_MIN_US)
    return int(pulse_us / 20000.0 * 1023)

def set_servo1(angle):
    servo1.duty(angle_to_duty(max(0, min(180, angle))))

def set_servo2(angle):
    servo2.duty(angle_to_duty(max(0, min(180, angle))))

def pump_on():
    relay.value(0 if RELAY_ACTIVE_LOW else 1)

def pump_off():
    relay.value(1 if RELAY_ACTIVE_LOW else 0)

def fire_detected():
    # Active LOW: sensor pulls D0 LOW when flame is in range
    return fire_pin.value() == 1

def smoke_detected():
    # Active LOW: sensor pulls D0 LOW when smoke threshold exceeded
    return smoke_pin.value() == 1

def set_rgb(r, g, b):
    r_pwm.duty(int(r / 255 * 1023))
    g_pwm.duty(int(g / 255 * 1023))
    b_pwm.duty(int(b / 255 * 1023))

def led_green():  set_rgb(0, 180, 0)
def led_yellow(): set_rgb(180, 100, 0)
def led_red():    set_rgb(255, 0, 0)
def led_off():    set_rgb(0, 0, 0)

def buzzer_on(freq=1500):
    buzzer.freq(freq)
    buzzer.duty(512)

def buzzer_off():
    buzzer.duty(0)

def read_dht():
    try:
        dht_sensor.measure()
        return dht_sensor.temperature(), dht_sensor.humidity()
    except OSError:
        return None, None

# ================================================================
# FIRE VERIFICATION
# Called once after CONFIRM_COUNT is reached.
# Reads the sensor VERIFY_COUNT more times.
# Every single read must return True — one clear read aborts.
# Pump and servo 2 will NOT activate if this returns False.
# ================================================================

def fire_verified():
    for i in range(VERIFY_COUNT):
        if not fire_detected():
            print(f"  Verify read {i+1}/{VERIFY_COUNT}: clear — false positive.")
            return False
        time.sleep_ms(VERIFY_DELAY_MS)
    return True

# ================================================================
# SPRAY SWEEP
# Called ONLY after fire_verified() returns True.
# Servo 2 sweeps 0°→180°→0° while pump sprays every angle.
# Fire sensor checked at end of each full pass.
# Returns when fire clears.
# ================================================================

def spray_sweep():
    angle = 0
    direction = 1
    passes = 0

    print("  Servo 2 moving to 0° start position...")
    set_servo2(0)
    time.sleep_ms(700)

    print("  Sweeping 0°→180° and back — spraying all angles...")

    while True:
        angle += SPRAY_STEP * direction
        set_servo2(angle)
        time.sleep_ms(SPRAY_DELAY_MS)

        if angle >= 180:
            angle = 180
            direction = -1
            passes += 1
            print(f"  Pass {passes} complete (at 180°) — checking fire sensor...")
            if not fire_detected():
                print("  Fire cleared.")
                break

        elif angle <= 0:
            angle = 0
            direction = 1
            passes += 1
            print(f"  Pass {passes} complete (at 0°) — checking fire sensor...")
            if not fire_detected():
                print("  Fire cleared.")
                break

# ================================================================
# STARTUP — safe state guaranteed before anything runs
# ================================================================

pump_off()          # relay de-energised
buzzer_off()
set_servo1(90)      # scanner centres
set_servo2(90)      # nozzle parks — will not move until fire verified
led_off()
time.sleep(1)

print("=" * 48)
print("  ESP32 Fire Suppression System — Online")
print(f"  Servo 1 (scanner)  GPIO{SERVO1_PIN}  — sweeping")
print(f"  Servo 2 (nozzle)   GPIO{SERVO2_PIN}  — parked at 90° [OFF]")
print(f"  Pump / relay       GPIO{RELAY_PIN}   — OFF")
print(f"  Fire sensor        GPIO{FIRE_PIN}")
print(f"  Smoke sensor       GPIO{SMOKE_PIN}")
print(f"  Buzzer             GPIO{BUZZER_PIN}")
print(f"  DHT11              GPIO{DHT_PIN}")
print(f"  RGB LED            R{RGB_R_PIN} / G{RGB_G_PIN} / B{RGB_B_PIN}")
print("=" * 48)
print(f"  Pump activates after {CONFIRM_COUNT} reads + {VERIFY_COUNT} verifications only.")
print("  Green=standby  Yellow=smoke  Red=fire\n")

# ================================================================
# MAIN LOOP
# ================================================================

scan_angle   = 90     # current servo 1 position
scan_dir     = 1      # sweep direction
confirm      = 0      # consecutive fire read counter
last_dht_ms  = 0
last_beep_ms = 0

led_green()

while True:
    now = time.ticks_ms()

    # ---- DHT11 non-blocking read ----
    if time.ticks_diff(now, last_dht_ms) >= DHT_INTERVAL_MS:
        temp, hum = read_dht()
        if temp is not None:
            print(f"[DHT11] {temp}C  {hum}% RH")
        else:
            print("[DHT11] Read error")
        last_dht_ms = now

    fire  = fire_detected()
    smoke = smoke_detected()

    # ---- Update fire confirmation counter ----
    if fire:
        confirm += 1
    else:
        confirm = 0

    # ==============================================================
    # DANGER STATE
    # Only reached after CONFIRM_COUNT consecutive fire reads.
    # Pump and servo 2 activate ONLY if fire_verified() is True.
    # ==============================================================
    if confirm >= CONFIRM_COUNT:
        locked_angle = scan_angle
        print(f"\n[FIRE] {CONFIRM_COUNT} consecutive reads — servo 1 at {locked_angle}°")
        print(f"  Verifying ({VERIFY_COUNT} reads × {VERIFY_DELAY_MS}ms)...")

        if not fire_verified():
            confirm = 0
            print("  False positive detected — pump stays OFF.\n")

        else:
            print("  FIRE VERIFIED.")
            print(f"  Servo 1 locked at {locked_angle}°")
            print("  Pump ON — servo 2 sweeping full 180°...")

            # Lock servo 1 at detection angle
            set_servo1(locked_angle)

            # Alert
            led_red()
            buzzer_on(1500)

            # Pump ON — activated here and only here
            pump_on()

            # Servo 2 sweeps full 0-180 range spraying all angles
            spray_sweep()

            # ---- Fire gone — shut everything down ----
            pump_off()
            buzzer_off()
            print("[FIRE] Suppressed. System resetting...\n")

            # 3 green flashes = all clear
            for _ in range(3):
                led_green()
                time.sleep_ms(200)
                led_off()
                time.sleep_ms(200)

            # Return both servos home
            set_servo2(90)
            set_servo1(90)
            time.sleep(1)

            # Reset all state
            scan_angle  = 90
            scan_dir    = 1
            confirm     = 0
            led_green()
            print("Standby resumed.")
            print("Servo 2 parked. Pump OFF.\n")

    # ==============================================================
    # WARNING STATE — smoke only, no fire
    # Servo 2 and pump not touched.
    # ==============================================================
    elif smoke:
        led_yellow()
        if time.ticks_diff(now, last_beep_ms) >= 800:
            buzzer_on(700)
            time.sleep_ms(100)
            buzzer_off()
            last_beep_ms = now
            print("[SMOKE] Smoke detected — pump OFF, servo 2 parked")

        scan_angle += SCAN_STEP * scan_dir
        if scan_angle >= 180:
            scan_angle = 180
            scan_dir   = -1
        elif scan_angle <= 0:
            scan_angle = 0
            scan_dir   = 1
        set_servo1(scan_angle)
        time.sleep_ms(SCAN_DELAY_MS)

    # ==============================================================
    # STANDBY STATE — all clear
    # Servo 2 and pump not touched.
    # ==============================================================
    else:
        led_green()
        buzzer_off()

        scan_angle += SCAN_STEP * scan_dir
        if scan_angle >= 180:
            scan_angle = 180
            scan_dir   = -1
        elif scan_angle <= 0:
            scan_angle = 0
            scan_dir   = 1
        set_servo1(scan_angle)
        time.sleep_ms(SCAN_DELAY_MS)
