import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import max30102
import hrcalc
from datetime import datetime, timedelta
import os
from collections import deque
from bluetooth_receiver import BluetoothReceiver

LOG_DIR = "./logs"  # Directory to store log files


# RMSSD calculation
def calculate_rmssd(rates):
    diffs = np.diff(rates)
    return np.sqrt(np.mean(diffs**2))


# HRSTD calculation
def calculate_hrstd(rates):
    return np.std(rates)


# Generate mock data (simulating heart rate values)
def generate_data():
    # 100 samples are read and used for HR/SpO2 calculation in a single loop
    red, ir = m.read_sequential()
    # TODO: should get IPM
    bpm = hrcalc.calc_hr_and_spo2(ir, red)

    return bpm


def save_log(bpm, current_log_file):
    if bpm < 0:
        return

    try:
        with open(current_log_file, "a") as log_file:
            # Get the current timestamp in a readable format
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Write the log with the timestamp
            log_file.write(f"{timestamp} - {bpm}\n")
    except IOError as e:
        print(f"Error saving raw data: {e}")


def get_data_from_log(current_log_file):
    # Define a time window of 1 minute
    time_window = timedelta(minutes=1)
    current_time = datetime.now()

    # Use deque to efficiently store lines within the last 30 seconds
    recent_lines = deque()

    with open(current_log_file, "r") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue

            # Extract the timestamp from the line
            try:
                timestamp_str, data = line.split(
                    " - ", 1)  # Split into timestamp and data
                log_time = datetime.strptime(timestamp_str,
                                             "%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue  # Skip lines that don't have the expected format

            # Check if the log is within the last 30 seconds
            if current_time - log_time <= time_window:
                recent_lines.append(data)  # Add the line to recent lines

    time_data, heart_rates = [], []
    for i, line in enumerate(recent_lines):
        values = line.split(" - ")
        time_data.append(i)
        heart_rates.append(int(values[0]))

    return time_data, heart_rates


# Update GUI with new data
def update_data(receiver, current_log_file):
    bpm = int(receiver.read_data())

    save_log(bpm, current_log_file)
    time_data, heart_rates = get_data_from_log(current_log_file)

    # Calculate metrics
    bpm_label.config(text=f"BPM: {bpm}")
    ipm_label.config(text=f"IPM: {int(bpm * 1.5)}")  # Example IPM calculation
    rmssd_label.config(text=f"RMSSD: {calculate_rmssd(heart_rates):.2f}")
    hrstd_label.config(text=f"HRSTD: {calculate_hrstd(heart_rates):.2f}")

    # Update plot with new data
    update_plot(time_data, heart_rates)

    # Schedule the next update
    root.after(1000, update_data(receiver,
                                 current_log_file))  # Update every second


def update_plot(time_data, heart_rates):
    ax.clear()  # Clear previous plot
    print(heart_rates)
    ax.plot(time_data, heart_rates, label="IPM / BPM",
            color='r')  # Draw a line for the heartbeat
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Heart Rate (BPM / IPM)")
    ax.set_title("Heartbeat over Time")
    ax.legend()

    canvas.draw()  # Redraw canvas to update the plot


# Example usage
if __name__ == "__main__":
    # Ensure the log directory exists
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    # Create a new log file with the current date and time
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    current_log_file = os.path.join(LOG_DIR, f"log_{timestamp}.log")
    with open(current_log_file, "w") as log_file:
        log_file.write(f"Log file created on {datetime.now()}\n")

    print(f"New log file created: {current_log_file}")

    # m = max30102.MAX30102()
    try:
        receiver = BluetoothReceiver()
        receiver.start_server()

        # Set up tkinter GUI
        root = tk.Tk()
        root.title("Heart Rate Monitor")

        # Labels for metrics
        bpm_label = ttk.Label(root, text="BPM: --")
        bpm_label.grid(row=0, column=0)
        ipm_label = ttk.Label(root, text="IPM: --")
        ipm_label.grid(row=1, column=0)
        rmssd_label = ttk.Label(root, text="RMSSD: --")
        rmssd_label.grid(row=2, column=0)
        hrstd_label = ttk.Label(root, text="HRSTD: --")
        hrstd_label.grid(row=3, column=0)

        # Create figure for the plot
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.set_xlim(0, 60)  # x-axis (30 data points)
        ax.set_ylim(0, 200)  # y-axis (light values between 0 and 1024)

        # Embed the plot in the tkinter window
        canvas = FigureCanvasTkAgg(fig, master=root)
        canvas.get_tk_widget().grid(row=0, column=1, rowspan=6)

        root.after(1000, update_data(
            receiver, current_log_file))  # Initial call to start the loop
        root.mainloop()

    except KeyboardInterrupt:
        print("Shutting down server...")
    finally:
        receiver.stop_server()
