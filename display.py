import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime, timedelta
import os
from collections import deque
from bluetooth_receiver import BluetoothReceiver
import threading
import queue
import json
import ast

LOG_DIR = "./logs"  # Directory to store log files

selected_data = 'bpm'


def save_log(data, current_log_file):
    try:
        with open(current_log_file, "a") as log_file:
            # Get the current timestamp in a readable format
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Write the log with the timestamp
            log_file.write(f"{timestamp} - {data}\n")
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
        formatted_data = ast.literal_eval(values[0])
        heart_rates.append(formatted_data)

    return time_data, heart_rates


def update_plot(time_data, heart_rates):
    bpm_data = [heart_rate['bpm'] for heart_rate in heart_rates]
    ipm_data = [heart_rate['ipm'] for heart_rate in heart_rates]
    ax.plot(time_data,
            bpm_data if selected_data == 'bpm' else ipm_data,
            label="IPM / BPM",
            color='r')  # Draw a line for the heartbeat
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Heart Rate (BPM / IPM)")
    ax.set_title("Heartbeat over Time")
    ax.legend()

    canvas.draw()  # Redraw canvas to update the plot


data = None


def data_receiver_thread(receiver, current_log_file):
    """
    Thread function for receiving data from the Bluetooth device.
    """
    global data

    while receiver:
        json_str = receiver.read_data()
        data = json.loads(json_str)
        if data.get('bpm', -1) >= 0:
            save_log(data, current_log_file)


def format_value(label, value, precision=2, invalid_placeholder="--"):
    """
    Helper function to format a value for display in the GUI.

    Args:
        label (str): The label to format (e.g., "BPM").
        value (float or int): The value to format.
        precision (int): The number of decimal places for formatting.
        invalid_placeholder (str): The placeholder for invalid values.

    Returns:
        str: Formatted label string.
    """
    if value < 0:
        return f"{label}: {invalid_placeholder}"
    if isinstance(value, (float, int)):
        return f"{label}: {value:.{precision}f}" if isinstance(
            value, float) else f"{label}: {value}"
    return f"{label}: {invalid_placeholder}"


def update_gui_with_threading(current_log_file):
    """
    Function to update the GUI, retrieving data from the queue.
    """

    global data

    raw_data = data.get('raw_data', [])
    bpm = data.get('bpm', -1)
    ipm = data.get('ipm', -1)
    rmssd = data.get('rmssd', -1)
    hrstd = data.get('hrstd', -1)

    print(data)

    # # Update labels using helper function
    # bpm_label.config(text=format_value("BPM", bpm))
    # ipm_label.config(text=format_value("IPM", ipm))
    # rmssd_label.config(text=format_value("RMSSD", rmssd))
    # hrstd_label.config(text=format_value("HRSTD", hrstd))

    # Update plot
    update_plot(raw_data)

    # Schedule the next GUI update
    root.after(1000, update_gui_with_threading, current_log_file)


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

    try:
        receiver = BluetoothReceiver()
        receiver.start_server()

        # Start the data receiving thread
        receiver_thread = threading.Thread(target=data_receiver_thread,
                                           args=(receiver, current_log_file),
                                           daemon=True)
        receiver_thread.start()

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

        # Start the GUI update loop
        root.after(1000, update_gui_with_threading, current_log_file)
        root.mainloop()

    except KeyboardInterrupt:
        print("Shutting down server...")
    finally:
        receiver.stop_server()
