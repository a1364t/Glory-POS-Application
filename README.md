# Glory POS Application

A custom Point‑of‑Sale (POS) controller application built in **Python** using **PyQt5**, designed to communicate with **Glory BrueBox / CDM (Cash Deposit Module) / ADM (Automatic Deposit Machine)** devices via SOAP.
The application provides a clean UI to manage sessions, deposits, dispensing, status checks, resets, and transaction cancellations — all without freezing the interface.

------------------------------------------------------------
🚀 FEATURES
------------------------------------------------------------

✅ Modern PyQt5 POS Interface
- Live connection indicator (Online / Offline / Error)
- Status header with color‑coded alerts
- Clean, intuitive layout for operations

✅ Complete Glory SOAP API Support
- OpenOperation
- OccupyOperation
- ReleaseOperation
- CloseOperation
- GetStatus
- ChangeOperation (Deposit / Dispense)
- ChangeCancelOperation
- ResetOperation

✅ Thread‑Safe Architecture
- 1‑second silent heartbeat in a background thread (no logs)
- Deposit / Dispense operation uses a worker thread
- Cancel works instantly even during deposit
- Reset supports long timeouts without freezing UI

✅ Smart Error Handling
- result 0 → OK
- result 5 → Device not occupied (warning)
- result 21 → Invalid session (warning)
- result None → Offline
- Logs: "⚠️ Sending request WITHOUT SessionID" when session missing

✅ Full Logging (except heartbeat)
- Full SOAP Request XML (blue)
- Full SOAP Response XML (green)
- Result logs (pink)
- Warnings (orange)
- Errors (red)

------------------------------------------------------------
📦 INSTALLATION
------------------------------------------------------------

Requirements:
- Python 3.10+
- Windows 10 or newer
- Libraries:
    pip install PyQt5 requests

------------------------------------------------------------
▶️ RUNNING THE APPLICATION
------------------------------------------------------------

Clone the repo:
    git clone https://github.com/a1364t/Glory-POS-Application.git

Enter folder:
    cd Glory-POS-Application

Run:
    python main.py

------------------------------------------------------------
📁 PROJECT STRUCTURE
------------------------------------------------------------

Glory-POS-Application/
│
├── main.py                 (GUI Application)
├── bruebox_client.py       (SOAP API client)
├── dist/main.exe           (PyInstaller EXE build)
├── build/                  (Build artifacts)
├── Command.txt             (Notes / XML samples)
└── README.md

------------------------------------------------------------
🏗️ BUILD EXE (OPTIONAL)
------------------------------------------------------------

Install PyInstaller:
    pip install pyinstaller

Build:
    pyinstaller --onefile --windowed main.py

EXE will appear in:
    dist/main.exe

------------------------------------------------------------
🧪 TESTING CHECKLIST
------------------------------------------------------------

✅ Check device online → heartbeat shows green  
✅ Open Session → Occupy → Deposit  
✅ Cancel during deposit to verify cancellation  
✅ Reset after test errors  
✅ Verify “Send WITHOUT SessionID” log when session ID empty  
✅ Offline detection updated every second  

------------------------------------------------------------
📌 FUTURE IMPROVEMENTS (OPTIONAL)
------------------------------------------------------------

- Live cassette inventory dashboard
- Auto log file saving
- Device event history panel


------------------------------------------------------------
👤 AUTHOR
------------------------------------------------------------

Alireza Talaei  
Infrastructure Project Engineer  
Sydney, Australia  

------------------------------------------------------------
🔒 LICENSE
------------------------------------------------------------

This project is private and intended for internal development and testing purposes only.