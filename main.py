# main.py
import sys
import os
import requests
from threading import Thread

from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QInputDialog
)
from PyQt5.QtGui import QColor, QIcon, QTextCharFormat, QTextCursor
from PyQt5.QtCore import QTimer, pyqtSignal

from bruebox_client import BrueBoxClient
from cloud_client import CloudClient


# ======================================================
# POS IDENTITY - Configuration for POS identification
# ======================================================
POS_ID = "POS-SYDNEY-002"        # Unique identifier for this POS terminal, must match the backend database
API_KEY = "REPLACE_WITH_KEY"    # Secret key for API authentication, must match the backend POS record

# ======================================================
# CLOUD CONFIG - Settings for cloud communication
# ======================================================
CLOUD_BASE_URL = "https://talaeia.pythonanywhere.com//api"  # Base URL for the cloud API endpoint
POLL_INTERVAL_MS = 3000  # Interval in milliseconds for polling the cloud for new commands


def mask_api_key(key: str) -> str:
    """Return masked API key for UI display"""
    if not key or len(key) < 8:
        return "****"
    return f"{key[:4]}…{key[-4:]}"


def get_resource_path(relative_path):
    """Get the absolute path to a resource, works for both development and PyInstaller exe"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # If not running as exe, use the current directory
        base_path = ""
    
    return os.path.join(base_path, relative_path)



class POSWindow(QWidget):
    """
    Main window for the Glory POS application.
    Handles user interface, FCC device communication via LAN, and cloud integration.
    """

    log_signal = pyqtSignal(str, str)  # Signal for logging messages with color
    status_signal = pyqtSignal(str, str)  # Signal for status updates with color

    def __init__(self):
        super().__init__()

        # --------------------------------------------------
        # BRUEBOX CLIENT - Handles LAN communication with FCC device
        # --------------------------------------------------
        # BrueBoxClient manages the connection to the cash recycler (FCC) over the local network
        self.client = BrueBoxClient()
        self.client.log_callback = lambda msg, col="black": self.log_signal.emit(msg, col)

        # Connect signals for UI updates
        self.log_signal.connect(self.log)
        self.status_signal.connect(self.set_status)

        # --------------------------------------------------
        # CLOUD CONFIG - Setup for cloud API communication
        # --------------------------------------------------
        # Configuration for sending/receiving commands from the cloud backend
        self.cloud_base_url = CLOUD_BASE_URL
        self.cloud_headers = {
            "X-POS-ID": POS_ID,      # POS identifier for API requests
            "X-API-KEY": API_KEY,    # API key for authentication
        }
        self.poll_interval_ms = POLL_INTERVAL_MS

        # --------------------------------------------------
        # CLOUD CLIENT - Manages cloud polling and command execution
        # --------------------------------------------------
        # CloudClient handles fetching commands from the cloud and executing them on the FCC device
        self.cloud_client = CloudClient(
            self.cloud_base_url,
            self.cloud_headers,
            self.client,  # Pass the BrueBoxClient for executing device commands
            lambda msg, col="black": self.log_signal.emit(msg, col),  # Log callback
            lambda text, color: self.status_signal.emit(text, color),  # Status callback
            self.update_cloud_circle  # Cloud connection status callback
        )

        # --------------------------------------------------
        # WINDOW SETUP - Configure the main application window
        # --------------------------------------------------
        self.setWindowTitle("Glory Developer POS (Alireza Talaei)")
        icon_path = get_resource_path("Images/Designer.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.setGeometry(200, 200, 800, 720)  # Position and size of the window

        layout = QVBoxLayout()  # Main vertical layout for the window

        # --------------------------------------------------
        # IP INPUT - Allow user to set FCC device IP address
        # --------------------------------------------------
        ip_row = QHBoxLayout()

        self.ip_input = QLineEdit("192.168.0.25")
        self.ip_input.setPlaceholderText("Enter FCC IP address")
        self.ip_input.setStyleSheet("font-size:16px; padding:5px;")
        ip_row.addWidget(self.ip_input)

        btn_set_ip = QPushButton("Set IP")
        btn_set_ip.setStyleSheet("font-size:16px; padding:8px;")
        btn_set_ip.setFixedWidth(120)
        btn_set_ip.clicked.connect(self.set_ip)  # Connect to IP setting method
        ip_row.addWidget(btn_set_ip)

        layout.addLayout(ip_row)
        

        # --------------------------------------------------
        # STATUS STRIP - Display connection and identity status
        # --------------------------------------------------
        status_row = QHBoxLayout()

        # LEFT COLUMN - Device and cloud connection indicators
        left_col = QVBoxLayout()

        self.circle = QLabel("● FCC Offline")  # FCC device connection status
        self.circle.setStyleSheet("font-size:20px; color:red; padding:4px;")
        left_col.addWidget(self.circle)

        self.cloud_circle = QLabel("☁ Cloud Waiting")  # Cloud connection status
        self.cloud_circle.setStyleSheet("font-size:20px; color:orange; padding:4px;")
        left_col.addWidget(self.cloud_circle)

        # RIGHT COLUMN - POS identity information
        right_col = QVBoxLayout()

        self.pos_id_label = QLabel(f"🆔 POS: {POS_ID}")  # Display POS ID
        self.pos_id_label.setStyleSheet("font-size:14px; color:#444; padding:8px 16px;")
        right_col.addWidget(self.pos_id_label)

        self.api_key_label = QLabel(f"🔑 Key: {mask_api_key(API_KEY)}")  # Display masked API key
        self.api_key_label.setStyleSheet("font-size:14px; color:#666; padding:8px 16px;")
        right_col.addWidget(self.api_key_label)

        # Assemble the status row
        status_row.addLayout(left_col)
        status_row.addStretch()      # Spacer to push right column to the right
        status_row.addLayout(right_col)

        layout.addLayout(status_row)

        # --------------------------------------------------
        # STATUS BAR - Main status display at the top
        # --------------------------------------------------
        self.status = QLabel("Idle")  # Current operation status
        self.status.setStyleSheet(
            "font-size:18px; background:#0078D7; color:white; padding:8px;"
        )
        layout.addWidget(self.status)

        # --------------------------------------------------
        # BUTTONS - Control buttons for FCC operations
        # --------------------------------------------------
        def add_row(buttons):
            row = QHBoxLayout()
            for b in buttons:
                b.setStyleSheet("font-size:16px; padding:8px;")
                row.addWidget(b)
            layout.addLayout(row)

        # Session management buttons
        self.btn_open = QPushButton("Open Session")
        self.btn_close = QPushButton("Close Session")
        add_row([self.btn_open, self.btn_close])

        # Device control buttons
        self.btn_occupy = QPushButton("Occupy")  # Lock device for exclusive use
        self.btn_release = QPushButton("Release")  # Release device lock
        add_row([self.btn_occupy, self.btn_release])

        # Transaction buttons
        self.btn_start = QPushButton("Deposit / Dispense")  # Start cash transaction
        self.btn_status = QPushButton("Get Status")  # Check device status
        self.btn_reset = QPushButton("Reset")  # Reset device
        self.btn_cancel = QPushButton("Cancel Transaction")  # Cancel current transaction
        add_row([self.btn_start, self.btn_status, self.btn_reset, self.btn_cancel])

        # --------------------------------------------------
        # BUTTON SIGNALS - Connect buttons to their handler methods
        # --------------------------------------------------
        self.btn_open.clicked.connect(self.open_session)
        self.btn_close.clicked.connect(self.close_session)
        self.btn_occupy.clicked.connect(self.occupy)
        self.btn_release.clicked.connect(self.release_device)
        self.btn_start.clicked.connect(self.start_deposit)
        self.btn_status.clicked.connect(self.check_status)
        self.btn_reset.clicked.connect(self.reset_device)
        self.btn_cancel.clicked.connect(self.cancel_transaction)

        # --------------------------------------------------
        # LOG WINDOW - Display application logs and messages
        # --------------------------------------------------
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setStyleSheet("font-size:14px;")
        layout.addWidget(self.log_box)

        self.setLayout(layout)

        # --------------------------------------------------
        # TIMERS - Background tasks for monitoring and polling
        # --------------------------------------------------
        # Heartbeat timer: Check FCC device status every second
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.threaded_heartbeat)
        self.status_timer.start(1000)

        # Cloud polling timer: Check for new cloud commands at regular intervals
        self.cloud_timer = QTimer(self)
        self.cloud_timer.timeout.connect(self.cloud_client.poll)
        self.cloud_timer.start(self.poll_interval_ms)

    # ======================================================
    # LOGGING - Handle UI logging with colored text
    # ======================================================
    def log(self, msg, color="black"):
        """Add a message to the log window with specified color."""
        if color == "pink":
            color = QColor(255, 40, 110)
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        cur = self.log_box.textCursor()
        cur.movePosition(QTextCursor.End)
        cur.insertText(msg + "\n", fmt)
        self.log_box.setTextCursor(cur)

    def set_status(self, text, color):
        """Update the main status bar with text and background color."""
        self.status.setText(text)
        self.status.setStyleSheet(
            f"font-size:18px; background:{color}; color:white; padding:8px;"
        )

    # ======================================================
    # FCC HEARTBEAT - Monitor FCC device connectivity
    # ======================================================
    def threaded_heartbeat(self):
        """Check FCC device status in a background thread and update UI indicator."""
        def worker():
            result, _ = self.client.status(silent=True)
            if result == "0":
                self.circle.setText("● FCC Online")
                self.circle.setStyleSheet("font-size:20px; color:green; padding:5px;")
            elif result is None:
                self.circle.setText("● FCC Offline")
                self.circle.setStyleSheet("font-size:20px; color:red; padding:5px;")
            else:
                self.circle.setText("● FCC Error")
                self.circle.setStyleSheet("font-size:20px; color:orange; padding:5px;")
        Thread(target=worker, daemon=True).start()

    # ======================================================
    # CLOUD INDICATOR - Update cloud connection status
    # ======================================================
    def update_cloud_circle(self, mode):
        """Update the cloud connection indicator based on connection status."""
        if mode == "online":
            self.cloud_circle.setText("☁ Cloud Connected")
            self.cloud_circle.setStyleSheet("font-size:20px; color:green; padding:5px;")
        elif mode == "error":
            self.cloud_circle.setText("☁ Cloud Disconnected")
            self.cloud_circle.setStyleSheet("font-size:20px; color:red; padding:5px;")
        else:
            self.cloud_circle.setText("☁ Cloud Waiting")
            self.cloud_circle.setStyleSheet("font-size:20px; color:orange; padding:5px;")





    # ======================================================
    # LOCAL BUTTON HANDLERS - Handle user button clicks for FCC operations
    # ======================================================
    def set_ip(self):
        """Update the IP address for connecting to the FCC device."""
        ip = self.ip_input.text().strip()
        self.client.set_ip(ip)
        self.set_status(f"IP set to {ip}", "#28a745")

    def open_session(self):
        """Open a new session with the FCC device."""
        sid, _ = self.client.open()
        if sid:
            self.log(f"Session opened → {sid}", "pink")
            self.set_status(f"Session: {sid}", "#0078D7")
        else:
            self.set_status("Open failed", "#d9534f")

    def occupy(self):
        """Occupy the FCC device for exclusive use."""
        result, _ = self.client.occupy()
        self.log(f"Occupy result = {result} (SID: {self.client.session_id})", "pink")
        self.set_status("Occupy OK" if result == "0" else "Occupy Error",
                        "#28a745" if result == "0" else "#d9534f")

    def release_device(self):
        """Release the FCC device from exclusive use."""
        result, _ = self.client.release()
        self.log(f"Release result = {result} (SID: {self.client.session_id})", "pink")
        self.set_status("Released" if result == "0" else "Release Error",
                        "#28a745" if result == "0" else "#d9534f")

    def close_session(self):
        """Close the current session with the FCC device."""
        result, _ = self.client.close()
        self.log(f"Close result = {result} (SID: {self.client.session_id})", "pink")
        self.set_status("Closed" if result == "0" else "Close Error",
                        "#28a745" if result == "0" else "#d9534f")

    def start_deposit(self):
        """Initiate a deposit or dispense transaction with user-specified amount."""
        amount, ok = QInputDialog.getInt(
            self,
            "Deposit / Dispense",
            "Enter amount in cents (negative = dispense):",
            value=0, min=-10_000_000, max=10_000_000
        )
        if not ok:
            return

        self.set_status("Processing...", "#ff9900")

        def worker():
            result, _ = self.client.change(amount)
            self.log_signal.emit(
                f"Change result = {result} (SID: {self.client.session_id})",
                "pink"
            )
            self.status_signal.emit("OK" if result == "0" else "Change Error",
                                    "#28a745" if result == "0" else "#d9534f")

        Thread(target=worker, daemon=True).start()

    def check_status(self):
        """Query the current status of the FCC device."""
        result, _ = self.client.status()
        self.log(f"Status result = {result} | SID={self.client.session_id}", "pink")
        if result == "0":
            self.set_status("Machine OK", "#28a745")
        elif result is None:
            self.set_status("Machine OFFLINE", "#d9534f")
        else:
            self.set_status("Machine ERROR", "#ff5900")

    def reset_device(self):
        """Reset the FCC device to its initial state."""
        result, _ = self.client.reset()
        self.log(f"Reset result = {result} (SID: {self.client.session_id})", "pink")
        self.set_status("Reset OK" if result == "0" else "Reset Error",
                        "#28a745" if result == "0" else "#d9534f")

    def cancel_transaction(self):
        """Cancel the current transaction on the FCC device."""
        result, _ = self.client.cancel_change()
        self.log(f"Cancel result = {result} (SID: {self.client.session_id})", "pink")
        self.set_status("Cancel OK" if result == "0" else "Cancel Error",
                        "#28a745" if result == "0" else "#d9534f")


if __name__ == "__main__":
    # Initialize and run the PyQt5 application
    app = QApplication(sys.argv)
    window = POSWindow()  # Create the main POS window
    window.show()  # Display the window
    sys.exit(app.exec_())  # Start the event loop and exit on close