# main.py
import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QInputDialog
)
from PyQt5.QtGui import QColor, QIcon, QTextCharFormat, QTextCursor
from PyQt5.QtCore import QTimer, pyqtSignal
from threading import Thread
from bruebox_client import BrueBoxClient


class POSWindow(QWidget):

    log_signal = pyqtSignal(str, str)
    status_signal = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.client = BrueBoxClient()

        # ✅ Thread-safe logging
        self.client.log_callback = lambda msg, col="black": self.log_signal.emit(msg, col)
        self.log_signal.connect(self.log)
        self.status_signal.connect(self.set_status)

        self.setWindowTitle("Glory POS (Alireza Talaei)")
        self.setWindowIcon(QIcon("Images/Designer.png"))  
        self.setGeometry(200, 200, 800, 700)

        layout = QVBoxLayout()

        # -----------------------------------------
        # IP + SET IP
        # -----------------------------------------
        self.ip_input = QLineEdit("192.168.0.25")
        self.ip_input.setPlaceholderText("Enter FCC IP address")
        self.ip_input.setStyleSheet("font-size:16px; padding:5px;")
        layout.addWidget(self.ip_input)

        self.btn_set_ip = QPushButton("Set IP")
        self.btn_set_ip.setStyleSheet("font-size:16px; padding:6px;")
        self.btn_set_ip.clicked.connect(self.set_ip)
        layout.addWidget(self.btn_set_ip)

        # -----------------------------------------
        # ONLINE / OFFLINE CIRCLE
        # -----------------------------------------
        self.circle = QLabel("● Offline")
        self.circle.setStyleSheet("font-size:20px; color:red; padding:5px;")
        layout.addWidget(self.circle)

        # -----------------------------------------
        # HEADER
        # -----------------------------------------
        self.status = QLabel("Idle")
        self.status.setStyleSheet("font-size:18px; background:#0078D7; color:white; padding:8px;")
        layout.addWidget(self.status)

        # -----------------------------------------
        # OPEN / CLOSE
        # -----------------------------------------
        row1 = QHBoxLayout()
        self.btn_open = QPushButton("Open Session")
        self.btn_close = QPushButton("Close Session")
        for b in (self.btn_open, self.btn_close):
            b.setStyleSheet("font-size:16px; padding:8px;")
            row1.addWidget(b)
        layout.addLayout(row1)

        # -----------------------------------------
        # OCCUPY / RELEASE
        # -----------------------------------------
        row2 = QHBoxLayout()
        self.btn_occupy = QPushButton("Occupy")
        self.btn_release = QPushButton("Release")
        for b in (self.btn_occupy, self.btn_release):
            b.setStyleSheet("font-size:16px; padding:8px;")
            row2.addWidget(b)
        layout.addLayout(row2)

        # -----------------------------------------
        # DEPOSIT / STATUS / RESET / CANCEL
        # -----------------------------------------
        row3 = QHBoxLayout()
        self.btn_start = QPushButton("Start Deposit / Dispense")
        self.btn_status = QPushButton("Get Status")
        self.btn_reset = QPushButton("Reset")
        self.btn_cancel = QPushButton("Cancel Transaction")

        for b in (self.btn_start, self.btn_status, self.btn_reset, self.btn_cancel):
            b.setStyleSheet("font-size:16px; padding:8px;")
            row3.addWidget(b)
        layout.addLayout(row3)

        # BUTTON CONNECTIONS
        self.btn_open.clicked.connect(self.open_session)
        self.btn_close.clicked.connect(self.close_session)
        self.btn_occupy.clicked.connect(self.occupy)
        self.btn_release.clicked.connect(self.release_device)
        self.btn_start.clicked.connect(self.start_deposit)
        self.btn_status.clicked.connect(self.check_status)
        self.btn_reset.clicked.connect(self.reset_device)
        self.btn_cancel.clicked.connect(self.cancel_transaction)

        # -----------------------------------------
        # LOG WINDOW
        # -----------------------------------------
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setStyleSheet("font-size:14px;")
        layout.addWidget(self.log_box)

        self.setLayout(layout)

        # -----------------------------------------
        # 1-second HEARTBEAT (silent threaded)
        # -----------------------------------------
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.threaded_heartbeat)
        self.status_timer.start(1000)

    # -----------------------------------------
    # LOGGING
    # -----------------------------------------
    def log(self, msg, color="black"):
        if color == "pink":
            color = QColor(255, 40, 110)

        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        cur = self.log_box.textCursor()
        cur.movePosition(QTextCursor.End)
        cur.insertText(msg + "\n", fmt)
        self.log_box.setTextCursor(cur)

    # -----------------------------------------
    # STATUS BAR
    # -----------------------------------------
    def set_status(self, text, color):
        self.status.setText(text)
        self.status.setStyleSheet(f"font-size:18px; background:{color}; color:white; padding:8px;")

    # -----------------------------------------
    # ONLINE / OFFLINE INDICATOR
    # -----------------------------------------
    def update_circle(self, mode):
        if mode == "online":
            self.circle.setText("● Online")
            self.circle.setStyleSheet("font-size:20px; color:green; padding:5px;")
        elif mode == "error":
            self.circle.setText("● Error")
            self.circle.setStyleSheet("font-size:20px; color:orange; padding:5px;")
        else:
            self.circle.setText("● Offline")
            self.circle.setStyleSheet("font-size:20px; color:red; padding:5px;")

    # -----------------------------------------
    # THREADED HEARTBEAT (NO LOGS)
    # -----------------------------------------
    def threaded_heartbeat(self):
        def worker():
            result, _ = self.client.status(silent=True)

            if result == "0":
                self.update_circle("online")
            elif result is None:
                self.update_circle("offline")
            else:
                self.update_circle("error")

        Thread(target=worker, daemon=True).start()

    # -----------------------------------------
    # Set IP
    # -----------------------------------------
    def set_ip(self):
        ip = self.ip_input.text().strip()
        self.client.set_ip(ip)
        self.set_status(f"IP set to {ip}", "#28a745")

    # -----------------------------------------
    # BUTTON HANDLERS
    # -----------------------------------------
    def open_session(self):
        sid, _ = self.client.open()
        if sid:
            self.log(f"Session opened → {sid}", "pink")
            self.set_status(f"Session: {sid}", "#0078D7")
        else:
            self.set_status("Open failed", "#d9534f")

    def occupy(self):
        result, _ = self.client.occupy()
        self.log(f"Occupy result = {result} (SID: {self.client.session_id})", "pink")
        self.set_status("Occupy OK" if result == "0" else "Occupy Error",
                        "#28a745" if result=="0" else "#d9534f")

    def release_device(self):
        result, _ = self.client.release()
        self.log(f"Release result = {result} (SID: {self.client.session_id})", "pink")
        self.set_status("Released" if result=="0" else "Release Error",
                        "#28a745" if result=="0" else "#d9534f")

    def close_session(self):
        result, _ = self.client.close()
        self.log(f"Close result = {result} (SID: {self.client.session_id})", "pink")
        self.set_status("Closed" if result=="0" else "Close Error",
                        "#28a745" if result=="0" else "#d9534f")

    def start_deposit(self):
        amount, ok = QInputDialog.getInt(
            self, "Deposit / Dispense",
            "Enter amount in cents (negative = dispense):",
            value=0, min=-10_000_000, max=10_000_000
        )
        if not ok:
            return

        def worker():
            result, _ = self.client.change(amount)
            self.log_signal.emit(f"Change result = {result} (SID: {self.client.session_id})", "pink")

            if result=="0":
                self.status_signal.emit("OK", "#28a745")
            else:
                self.status_signal.emit("Change Error", "#d9534f")

        Thread(target=worker, daemon=True).start()
        self.set_status("Processing...", "#ff9900")

    def check_status(self):
        result, xml = self.client.status()
        self.log(f"Status result = {result} | SID={self.client.session_id}", "pink")

        if result=="0":
            self.set_status("Machine OK", "#28a745")
        elif result is None:
            self.set_status("Machine OFFLINE", "#d9534f")
        else:
            self.set_status("Machine ERROR", "#ff5900")

    def reset_device(self):
        result, xml = self.client.reset()
        self.log(f"Reset result = {result} (SID: {self.client.session_id})", "pink")

        if result=="0":
            self.set_status("Reset OK", "#28a745")
        elif result is None:
            self.set_status("Reset Failed", "#d9534f")
        else:
            self.set_status("Reset Error", "#ff5900")

    def cancel_transaction(self):
        result, xml = self.client.cancel_change()
        self.log(f"Cancel result = {result} (SID: {self.client.session_id})", "pink")

        if result=="0":
            self.set_status("Cancel OK", "#28a745")
        elif result is None:
            self.set_status("Cancel Failed", "#d9534f")
        else:
            self.set_status("Cancel Error", "#ff5900")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = POSWindow()
    window.show()
    sys.exit(app.exec_())