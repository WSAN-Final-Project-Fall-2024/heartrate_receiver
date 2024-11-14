import tkinter as tk
from tkinter import ttk
import serial
import time
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Update with the Bluetooth serial port
ser = serial.Serial("/dev/rfcomm0", 115200)  # Replace with your Bluetooth port

# Metrics calculation parameters
heart_rates = []
window_size = 4  # Can be adjusted for averaging
time_data = []  # List to store time data for plotting


# RMSSD calculation
def calculate_rmssd(rates):
    diffs = np.diff(rates)
    return np.sqrt(np.mean(diffs**2))


# HRSTD calculation
def calculate_hrstd(rates):
    return np.std(rates)


# Update GUI with new data
def update_data():
    global heart_rates, time_data

    if ser.in_waiting:
        data = ser.readline().decode().strip()
        print(data)  # For debugging

        try:
            ir_value, bpm, avg_bpm = parse_data(data)  # Parse incoming data

            # Append heart rate data
            heart_rates.append(avg_bpm)
            time_data.append(
                time.time()
            )  # Store the current time for x-axis of the plot

            if len(heart_rates) > window_size:
                heart_rates.pop(0)
                time_data.pop(0)  # Remove old time data to maintain window size

            # Calculate metrics
            bpm_label.config(text=f"BPM: {bpm}")
            avg_bpm_label.config(text=f"Avg BPM: {avg_bpm}")
            ipm_label.config(text=f"IPM: {int(bpm * 1.5)}")  # Example IPM calculation
            rmssd_label.config(text=f"RMSSD: {calculate_rmssd(heart_rates):.2f}")
            hrstd_label.config(text=f"HRSTD: {calculate_hrstd(heart_rates):.2f}")

            # Update plot with new data
            update_plot()

        except ValueError:
            pass  # Ignore parsing errors

    root.after(1000, update_data)  # Schedule next update


def update_plot():
    ax.clear()  # Clear previous plot
    ax.plot(
        time_data, heart_rates, label="Heart Rate", color="r"
    )  # Draw a line for the heartbeat
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Heart Rate (BPM)")
    ax.set_title("Heartbeat over Time")
    ax.legend()

    canvas.draw()  # Redraw canvas to update the plot


def parse_data(data):
    parts = data.split(",")
    ir_value = int(parts[0].split("=")[1])
    bpm = float(parts[1].split("=")[1])
    avg_bpm = int(parts[2].split("=")[1])
    return ir_value, bpm, avg_bpm


# Set up tkinter GUI
root = tk.Tk()
root.title("Heart Rate Monitor")

# Labels for metrics
bpm_label = ttk.Label(root, text="BPM: --")
bpm_label.grid(row=0, column=0)
avg_bpm_label = ttk.Label(root, text="Avg BPM: --")
avg_bpm_label.grid(row=1, column=0)
ipm_label = ttk.Label(root, text="IPM: --")
ipm_label.grid(row=2, column=0)
rmssd_label = ttk.Label(root, text="RMSSD: --")
rmssd_label.grid(row=3, column=0)
hrstd_label = ttk.Label(root, text="HRSTD: --")
hrstd_label.grid(row=4, column=0)

# Create figure for the plot
fig, ax = plt.subplots(figsize=(6, 4))
ax.set_xlabel("Time (s)")
ax.set_ylabel("Heart Rate (BPM)")
ax.set_title("Heartbeat over Time")

# Embed the plot in the tkinter window
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().grid(row=0, column=1, rowspan=6)

# Start the GUI loop
root.after(1000, update_data)  # Initial call to start the loop
root.mainloop()
