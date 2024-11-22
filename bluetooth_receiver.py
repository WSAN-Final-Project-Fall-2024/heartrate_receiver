import bluetooth
import subprocess
import atexit


class BluetoothReceiver:

    def __init__(self, port=1):
        """
        Initialize the BluetoothReceiver object.

        Args:
            port (int): RFCOMM port to listen on. Default is 1.
        """
        self.port = port
        self.server_sock = None
        self.client_sock = None
        self.client_info = None

    def enable_bluetooth(self):
        """Enable the Bluetooth device."""
        try:
            subprocess.run(["sudo", "hciconfig", "hci0", "up"], check=True)
            print("Bluetooth device hci0 is now up.")
        except subprocess.CalledProcessError:
            print("Failed to turn on Bluetooth device hci0.")

    def disable_bluetooth(self):
        """Disable the Bluetooth device."""
        try:
            subprocess.run(["sudo", "hciconfig", "hci0", "down"], check=True)
            print("Bluetooth device hci0 is now down.")
        except subprocess.CalledProcessError:
            print("Failed to turn off Bluetooth device hci0.")

    def start_server(self):
        """Start the Bluetooth server and listen for a client connection."""
        self.enable_bluetooth()

        # Retrieve the MAC address of the Bluetooth adapter on the server
        server_mac_address = bluetooth.read_local_bdaddr()[0]
        print(f"Server MAC Address: {server_mac_address}")

        # Create and bind the server socket
        self.server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        try:
            self.server_sock.bind(("", self.port))
            self.server_sock.listen(1)
            print(f"Listening for connections on RFCOMM channel {self.port}")

            # Accept a client connection
            self.client_sock, self.client_info = self.server_sock.accept()
            print(f"Accepted connection from {self.client_info}")
        except bluetooth.BluetoothError as e:
            print(f"Failed to start server: {e}")
            self.cleanup()

    def read_data(self):
        """
        Read data sent by the client.

        Returns:
            str: The received data as a string.
        """
        if self.client_sock:
            try:
                data = self.client_sock.recv(1024)
                return data.decode("utf-8") if data else None
            except Exception as e:
                print(f"An error occurred while reading data: {e}")
        else:
            print("No client connected. Unable to read data.")
        return None

    def stop_server(self):
        """Stop the Bluetooth server and clean up resources."""
        if self.client_sock:
            try:
                self.client_sock.close()
                print("Client socket closed.")
            except Exception as e:
                print(f"Error while closing client socket: {e}")

        if self.server_sock:
            try:
                self.server_sock.close()
                print("Server socket closed.")
            except Exception as e:
                print(f"Error while closing server socket: {e}")

        self.disable_bluetooth()

    def cleanup(self):
        """Clean up resources if an error occurs."""
        self.stop_server()


# Register the disable_bluetooth function to run at script exit
atexit.register(BluetoothReceiver.disable_bluetooth, BluetoothReceiver)

# # Example usage
# if __name__ == "__main__":
#     receiver = BluetoothReceiver()

#     try:
#         receiver.start_server()

#         # Continuously read data from the client
#         while True:
#             data = receiver.read_data()
#             if data:
#                 print(f"Received: {data}")
#     except KeyboardInterrupt:
#         print("Shutting down server...")
#     finally:
#         receiver.stop_server()
