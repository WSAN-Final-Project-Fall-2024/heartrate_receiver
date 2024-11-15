import bluetooth
import subprocess
import atexit

# Function to enable Bluetooth
def enable_bluetooth():
    try:
        subprocess.run(["sudo", "hciconfig", "hci0", "up"], check=True)
        print("Bluetooth device hci0 is now up.")
    except subprocess.CalledProcessError:
        print("Failed to turn on Bluetooth device hci0.")

# Function to disable Bluetooth
def disable_bluetooth():
    try:
        subprocess.run(["sudo", "hciconfig", "hci0", "down"], check=True)
        print("Bluetooth device hci0 is now down.")
    except subprocess.CalledProcessError:
        print("Failed to turn off Bluetooth device hci0.")

# Register the disable_bluetooth function to run at script exit
atexit.register(disable_bluetooth)

# Enable Bluetooth device hci0
enable_bluetooth()

# Server's Bluetooth MAC address (replace with actual server address)
server_address = "2C:CF:67:04:9D:D7"  # Replace with your server's Bluetooth MAC address
port = 1  # The RFCOMM port on the server (commonly set to 1)

# Set up a Bluetooth RFCOMM client socket
client_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
try:
    # Connect to the server using the server address and port
    client_sock.connect((server_address, port))
    print(f"Connected to server at {server_address} on port {port}", flush=True)

    # Send data to the server
    try:
        while True:
            # Replace this with dynamic data or input to send continuously
            data_to_send = input("Enter data to send (or 'exit' to quit): ")
            if data_to_send.lower() == "exit":
                break
            client_sock.send(data_to_send)
            print(f"Sent: {data_to_send}", flush=True)

    except Exception as e:
        print(f"An error occurred while sending data: {e}", flush=True)

finally:
    # Ensure the client socket is closed
    client_sock.close()
    print("Disconnected from the server", flush=True)
