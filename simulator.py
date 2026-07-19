#!/usr/bin/env python3
import time
import math
import random
import sys

# Attempt to import serial for real hardware/Proteus UART interfacing
try:
    import serial
    # Configure for Raspberry Pi primary UART pin mapping (TX=GPIO14/Pin8)
    ser = serial.Serial('/dev/ttyS0', 115200, timeout=1)
    UART_AVAILABLE = True
except ImportError:
    UART_AVAILABLE = False
    print("Warning: pyserial not found. Outputting to stdout only.", file=sys.stderr)

class VitalsSimulator:
    def __init__(self):
        # Initial baseline states
        self.state = "STABLE"  # Options: STABLE, WALKING, EXERCISING, ANXIOUS
        self.state_timer = 0
        
        # Physiological baselines
        self.hr = 72.0
        self.spo2 = 98.0
        self.temp = 36.5
        self.time_step = 0.0

    def update_state(self):
        """Simulates changing user activities over time to test ESP32 thresholds."""
        self.state_timer += 1
        if self.state_timer > 30:  # Switch state roughly every 30 iterations
            self.state_timer = 0
            self.state = random.choice(["STABLE", "WALKING", "EXERCISING", "STABLE"])
            print(f"\n[SYSTEM ALERT] Simulator changed activity state to: {self.state}\n")

    def generate_vitals(self):
        """Calculates physically correlated vital data based on current state."""
        self.time_step += 0.2
        self.update_state()

        # 1. State-Based Target Biometrics & Motion Tracking
        if self.state == "STABLE":
            target_hr = random.uniform(65.0, 74.0)
            target_spo2 = random.uniform(97.5, 99.5)
            target_temp = random.uniform(36.4, 36.7)
            motion_str = "STABLE"
        elif self.state == "WALKING":
            target_hr = random.uniform(85.0, 95.0)
            target_spo2 = random.uniform(96.0, 98.5)
            target_temp = random.uniform(36.7, 37.0)
            motion_str = "WALKING"
        elif self.state == "EXERCISING":
            target_hr = random.uniform(115.0, 135.0)
            target_spo2 = random.uniform(94.5, 96.5)  # Slight drop during heavy exertion
            target_temp = random.uniform(37.1, 37.6)
            motion_str = "RUNNING"
        else:
            target_hr, target_spo2, target_temp, motion_str = 72.0, 98.0, 36.5, "STABLE"

        # 2. Smooth Vitals Interpolation (Prevents unrealistic value jumps)
        self.hr += (target_hr - self.hr) * 0.15
        self.spo2 += (target_spo2 - self.spo2) * 0.1
        self.temp += (target_temp - self.temp) * 0.05

        # 3. Dynamic Synthesized ECG Signal Gen (Math Wave Modeling)
        # Combines a baseline drift with a rapid simulated QRS heart beat complex
        heart_freq_hz = self.hr / 60.0
        ecg_baseline = 1.2 + 0.1 * math.sin(self.time_step * 0.5)  # Respiratory baseline wander
        
        # Periodic heartbeat pulse calculation
        pulse_phase = (self.time_step * heart_freq_hz * 2 * math.pi) % (2 * math.pi)
        if 0.0 <= pulse_phase < 0.4:
            # Simulate the R-wave spike of the QRS complex
            ecg_signal = ecg_baseline + (2.5 * math.sin((pulse_phase / 0.4) * math.pi))
        else:
            # T-wave or resting state
            ecg_signal = ecg_baseline + (0.15 * math.sin(pulse_phase))

        return int(self.hr), int(self.spo2), round(self.temp, 1), round(ecg_signal, 2), motion_str

    def run(self):
        print("=============================================")
        print(" Upgraded Wearable Vitals Simulator Active   ")
        print(" Sending Format: HR,SPO2,TEMP,ECG,MOTION      ")
        print("=============================================")
        
        try:
            while True:
                hr, spo2, temp, ecg, motion = self.generate_vitals()
                
                # Assemble CSV Payload packet
                payload = f"{hr},{spo2},{temp},{ecg},{motion}\n"
                
                # Print output telemetry dashboard to terminal
                sys.stdout.write(f"\r[Telemetry Out] -> HR: {hr}bpm | SpO2: {spo2}% | Temp: {temp}°C | ECG: {ecg}V | State: {motion:<8}")
                sys.stdout.flush()
                
                # Transmit over UART wire to the Proteus ESP32 RX Pin
                if UART_AVAILABLE:
                    ser.write(payload.encode('utf-8'))
                
                # 1 Hz data rate matches your ESP32 display refresh window perfectly
                time.sleep(1.0)
                
        except KeyboardInterrupt:
            print("\nSimulation streaming safely terminated.")
            if UART_AVAILABLE:
                ser.close()

if __name__ == "__main__":
    simulator = VitalsSimulator()
    simulator.run()
