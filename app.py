#!/usr/bin/env python3
import time
import math
import random
import threading
from flask import Flask, render_markup, render_template_string
from flask_socketio import SocketIO

# Initialize Flask app and SocketIO for real-time web streaming
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

class VitalsSimulator:
    def __init__(self):
        self.state = "STABLE"
        self.state_timer = 0
        self.hr = 72.0
        self.spo2 = 98.0
        self.temp = 36.5
        self.time_step = 0.0

    def update_vitals(self):
        """Calculates physically correlated vital data."""
        self.time_step += 0.2
        self.state_timer += 1
        
        if self.state_timer > 30:
            self.state_timer = 0
            self.state = random.choice(["STABLE", "WALKING", "EXERCISING", "STABLE"])

        if self.state == "STABLE":
            target_hr, target_spo2, target_temp = random.uniform(65, 74), random.uniform(97.5, 99.5), random.uniform(36.4, 36.7)
        elif self.state == "WALKING":
            target_hr, target_spo2, target_temp = random.uniform(85, 95), random.uniform(96.0, 98.5), random.uniform(36.7, 37.0)
        elif self.state == "EXERCISING":
            target_hr, target_spo2, target_temp = random.uniform(115, 135), random.uniform(94.5, 96.5), random.uniform(37.1, 37.6)
        else:
            target_hr, target_spo2, target_temp = 72.0, 98.0, 36.5

        self.hr += (target_hr - self.hr) * 0.15
        self.spo2 += (target_spo2 - self.spo2) * 0.1
        self.temp += (target_temp - self.temp) * 0.05

        # ECG Complex math modeling
        heart_freq_hz = self.hr / 60.0
        ecg_baseline = 1.2 + 0.1 * math.sin(self.time_step * 0.5)
        pulse_phase = (self.time_step * heart_freq_hz * 2 * math.pi) % (2 * math.pi)
        
        if 0.0 <= pulse_phase < 0.4:
            ecg_signal = ecg_baseline + (2.5 * math.sin((pulse_phase / 0.4) * math.pi))
        else:
            ecg_signal = ecg_baseline + (0.15 * math.sin(pulse_phase))

        return {
            "hr": int(self.hr),
            "spo2": int(self.spo2),
            "temp": round(self.temp, 1),
            "ecg": round(ecg_signal, 2),
            "motion": "RUNNING" if self.state == "EXERCISING" else self.state
        }

simulator = VitalsSimulator()

def data_stream_thread():
    """Background thread that continuously generates data and broadcasts it over WebSockets."""
    while True:
        data = simulator.update_vitals()
        # Emit data instantly to the website interface
        socketio.emit('vitals_update', data)
        time.sleep(1.0) # Matches hardware display loop

# Embedded Dashboard HTML Page
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Wearable 5-Vitals Web Simulation</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.socketio.io/4.5.4/socketio.min.js"></script>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; background: #121214; color: #e1e1e6; margin: 20px; }
        .header { text-align: center; margin-bottom: 30px; border-bottom: 2px solid #29292e; padding-bottom: 10px; }
        .dashboard-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(450px, 1fr)); gap: 20px; }
        .card { background: #1d1d22; border-radius: 8px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); border: 1px solid #29292e; }
        .value-display { font-size: 2.5rem; font-weight: bold; color: #00e676; margin-top: 10px; }
        .status-badge { display: inline-block; padding: 5px 15px; border-radius: 20px; background: #323238; font-weight: bold; color: #ffca28; }
        canvas { max-height: 220px; }
    </style>
</head>
<body>

    <div class="header">
        <h1>Wearable 5-Vitals Monitoring Web Dashboard</h1>
        <p>Current Simulation State: <span id="motion-state" class="status-badge">STABLE</span></p>
    </div>

    <div class="dashboard-grid">
        <!-- Heart Rate Card -->
        <div class="card">
            <h3>Heart Rate (BPM)</h3>
            <div id="hr-val" class="value-display">--</div>
            <canvas id="hrChart"></canvas>
        </div>

        <!-- SpO2 Card -->
        <div class="card">
            <h3>SpO2 (%)</h3>
            <div id="spo2-val" class="value-display" style="color: #00b0ff;">--</div>
            <canvas id="spo2Chart"></canvas>
        </div>

        <!-- Temperature Card -->
        <div class="card">
            <h3>Body Temperature (°C)</h3>
            <div id="temp-val" class="value-display" style="color: #ff5252;">--</div>
            <canvas id="tempChart"></canvas>
        </div>

        <!-- ECG Wave Card -->
        <div class="card">
            <h3>ECG Telemetry (V)</h3>
            <div id="ecg-val" class="value-display" style="color: #e040fb; font-size: 1.5rem;">--</div>
            <canvas id="ecgChart"></canvas>
        </div>
    </div>

    <script>
        const socket = io();

        // Helper function to create line charts
        function createChart(canvasId, label, color) {
            return new Chart(document.getElementById(canvasId), {
                type: 'line',
                data: {
                    labels: Array(15).fill(''),
                    datasets: [{
                        label: label,
                        data: Array(15).fill(null),
                        borderColor: color,
                        tension: 0.3,
                        borderWidth: 2,
                        pointRadius: 2
                    }]
                },
                options: {
                    scales: { y: { grid: { color: '#29292e' } }, x: { display: false } },
                    plugins: { legend: { display: false } }
                }
            });
        }

        // Initialize 4 separate charts for our telemetry values
        const hrChart = createChart('hrChart', 'BPM', '#00e676');
        const spo2Chart = createChart('spo2Chart', '%', '#00b0ff');
        const tempChart = createChart('tempChart', '°C', '#ff5252');
        const ecgChart = createChart('ecgChart', 'V', '#e040fb');

        function updateChartData(chart, newValue) {
            chart.data.datasets[0].data.shift();
            chart.data.datasets[0].data.push(newValue);
            chart.update('none'); // Update without full animation loop for high speed layout
        }

        // Handle socket update events from python script
        socket.on('vitals_update', function(data) {
            // Update Text Figures
            document.getElementById('hr-val').innerText = data.hr + " bpm";
            document.getElementById('spo2-val').innerText = data.spo2 + " %";
            document.getElementById('temp-val').innerText = data.temp + " °C";
            document.getElementById('ecg-val').innerText = data.ecg + " V";
            document.getElementById('motion-state').innerText = data.motion;

            // Shift Graphic Plots
            updateChartData(hrChart, data.hr);
            updateChartData(spo2Chart, data.spo2);
            updateChartData(tempChart, data.temp);
            updateChartData(ecgChart, data.ecg);
        });
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

if __name__ == '__main__':
    # Start the simulation value loop safely in a separate thread
    threading.Thread(target=data_stream_thread, daemon=True).start()
    # Run server locally on Port 5000
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
