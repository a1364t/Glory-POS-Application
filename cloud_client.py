# cloud_client.py
"""
Client for handling cloud-based command polling and execution.
Communicates with a cloud API to receive commands and execute them on the local BrueBox device.
"""

import requests
from threading import Thread


class CloudClient:
    """
    Handles polling a cloud API for commands and executing them on the BrueBox device.
    Manages command execution and result reporting back to the cloud.
    """

    def __init__(self, base_url, headers, bruebox_client, log_callback, status_callback, update_cloud_circle_callback):
        """
        Initialize the cloud client with connection details and callbacks.
        
        Args:
            base_url (str): Base URL for the cloud API
            headers (dict): HTTP headers for API requests (POS ID, API key)
            bruebox_client: Instance of BrueBoxClient for device operations
            log_callback: Function to call for logging messages
            status_callback: Function to call for status updates
            update_cloud_circle_callback: Function to update cloud connection indicator
        """
        self.base_url = base_url
        self.headers = headers
        self.bruebox_client = bruebox_client
        self.log_callback = log_callback
        self.status_callback = status_callback
        self.update_cloud_circle_callback = update_cloud_circle_callback
        self.http = requests.Session()  # Persistent session for API calls
        self.poll_interval_ms = 3000  # Polling interval (set but not used here)

    def poll(self):
        """
        Poll the cloud API for new commands in a background thread.
        Fetches pending commands and executes them on the device.
        """
        def worker():
            try:
                # Fetch next command from cloud
                r = self.http.get(
                    f"{self.base_url}/fetch/",
                    headers=self.headers,
                    timeout=5
                )
                r.raise_for_status()
                data = r.json()
                self.update_cloud_circle_callback("online")  # Update UI indicator
            except Exception:
                self.update_cloud_circle_callback("error")  # Connection failed
                return

            if not data or not data.get("command"):
                return  # No command available

            # Notify UI that command is being processed
            self.status_callback(
                f"Cloud: {data['command']} processing...",
                "#ff9900"
            )

            # Execute the command on the device
            self.execute_command(
                data["id"],
                data["command"],
                data.get("amount")
            )

        Thread(target=worker, daemon=True).start()

    def execute_command(self, cmd_id, command, amount):
        """
        Execute a command received from the cloud on the BrueBox device.
        
        Args:
            cmd_id (str): Unique command ID from cloud
            command (str): Command type (OPEN, OCCUPY, etc.)
            amount (int, optional): Amount for CHANGE commands
        """
        result = ""

        try:
            if command == "OPEN":
                # Open a new session with the device
                sid, _ = self.bruebox_client.open()
                if sid:
                    result = "0"
                    self.log_callback(f"[CLOUD] Open result = 0 (SID: {sid})", "pink")
                    self.status_callback(f"Session: {sid}", "#0078D7")

            elif command == "OCCUPY":
                # Lock device for exclusive use
                result, _ = self.bruebox_client.occupy()
                self.log_callback(f"[CLOUD] Occupy result = {result} (SID: {self.bruebox_client.session_id})", "pink")

            elif command == "RELEASE":
                # Release device from exclusive use
                result, _ = self.bruebox_client.release()
                self.log_callback(f"[CLOUD] Release result = {result} (SID: {self.bruebox_client.session_id})", "pink")

            elif command == "CLOSE":
                # Close the current session
                result, _ = self.bruebox_client.close()
                self.log_callback(f"[CLOUD] Close result = {result} (SID: {self.bruebox_client.session_id})", "pink")

            elif command == "STATUS":
                # Check device status
                result, _ = self.bruebox_client.status()
                self.log_callback(f"[CLOUD] Status result = {result} (SID: {self.bruebox_client.session_id})", "pink")

            elif command == "RESET":
                # Reset device to initial state
                result, _ = self.bruebox_client.reset()
                self.log_callback(f"[CLOUD] Reset result = {result} (SID: {self.bruebox_client.session_id})", "pink")

            elif command == "CANCEL":
                # Cancel current transaction
                result, _ = self.bruebox_client.cancel_change()
                self.log_callback(f"[CLOUD] Cancel result = {result} (SID: {self.bruebox_client.session_id})", "pink")

            elif command == "CHANGE":
                # Perform deposit/dispense operation
                result, _ = self.bruebox_client.change(amount or 0)
                self.log_callback(
                    f"[CLOUD] Change amount={amount} result = {result} (SID: {self.bruebox_client.session_id})",
                    "pink"
                )

            # Update UI status
            if result == "0":
                self.status_callback("OK", "#28a745")
            else:
                self.status_callback("Error", "#d9534f")

        except Exception as e:
            self.log_callback(f"[CLOUD] Execution error: {e}", "red")
            self.status_callback("Execution Error", "#d9534f")

        # Post execution result back to cloud
        try:
            self.http.post(
                f"{self.base_url}/result/{cmd_id}/",
                headers=self.headers,
                json={
                    "status": "DONE" if result == "0" else "FAILED",
                    "result_code": result,
                    "result_text": "",
                },
                timeout=5
            )
        except Exception:
            self.update_cloud_circle_callback("error")