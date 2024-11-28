import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from bluetooth_receiver import BluetoothReceiver
import threading
import json


def update_plot(raw_data):
    print(raw_data)
    ax.clear()
    ax.plot(range(len(raw_data)), raw_data, label="IPM / BPM",
            color='r')  # Draw a line for the heartbeat
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Heart Rate (BPM / IPM)")
    ax.set_title("Heartbeat over Time")
    ax.legend()

    canvas.draw()  # Redraw canvas to update the plot


data = None


def data_receiver_thread(receiver):
    """
    Thread function for receiving data from the Bluetooth device.
    """
    global data

    while receiver:
        json_str = receiver.read_data()
        if json_str:
            data = json.loads(json_str)


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

    if data:
        raw_data = data.get('raw_value', [])
        bpm = data.get('bpm', -1)
        ipm = data.get('ipm', -1)
        rmssd = data.get('rmssd', -1)
        hrstd = data.get('hrstd', -1)

        # Update labels using helper function
        bpm_label.config(text=format_value("BPM", bpm))
        ipm_label.config(text=format_value("IPM", ipm))
        rmssd_label.config(text=format_value("RMSSD", rmssd))
        hrstd_label.config(text=format_value("HRSTD", hrstd))

        # Update plot
        update_plot(raw_data)

    # Schedule the next GUI update
    root.after(1000, update_gui_with_threading, current_log_file)


# Example usage
if __name__ == "__main__":
    try:
        receiver = BluetoothReceiver()
        receiver.start_server()

        # Start the data receiving thread
        receiver_thread = threading.Thread(target=data_receiver_thread,
                                           args=(receiver),
                                           daemon=True)
        receiver_thread.start()

        # Set up tkinter GUI
        root = tk.Tk()
        root.title("Heart Rate Monitor")
        label_font = ("Helvetica", 14)

        # Labels for metrics
        bpm_label = ttk.Label(root, text="BPM: --", width=20, font=label_font)
        bpm_label.grid(row=0, column=0, sticky='w', padx=10, pady=5)
        ipm_label = ttk.Label(root, text="IPM: --", width=20, font=label_font)
        ipm_label.grid(row=1, column=0, sticky='w', padx=10, pady=5)
        rmssd_label = ttk.Label(root,
                                text="RMSSD: --",
                                width=20,
                                font=label_font)
        rmssd_label.grid(row=2, column=0, sticky='w', padx=10, pady=5)
        hrstd_label = ttk.Label(root,
                                text="HRSTD: --",
                                width=20,
                                font=label_font)
        hrstd_label.grid(row=3, column=0, sticky='w', padx=10, pady=5)

        # Create figure for the plot
        fig, ax = plt.subplots(figsize=(12, 6))

        # Embed the plot in the tkinter window
        canvas = FigureCanvasTkAgg(fig, master=root)
        canvas.get_tk_widget().grid(row=0, column=1, rowspan=6)

        # Start the GUI update loop
        root.after(1000, update_gui_with_threading)
        root.mainloop()

    except KeyboardInterrupt:
        print("Shutting down server...")
    finally:
        receiver.stop_server()
