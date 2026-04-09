# Glory POS Application

A custom Point‑of‑Sale (POS) controller application built in **Python** using **PyQt5**, designed to communicate with **Glory BrueBox / CDM (Cash Deposit Module)/ ADM (Automatic Deposit Machine)** devices via SOAP.
The application provides a clean UI to manage sessions, deposits, dispensing, status checks, resets, and transaction cancellations — all without freezing the interface.

**NEW:** Now includes cloud integration for remote command execution and monitoring.

------------------------------------------------------------
🚀 FEATURES
------------------------------------------------------------

✅ Modern PyQt5 POS Interface  
- Live connection indicator (Online / Offline / Error)  
- Cloud connection status indicator
- Status header with color-coded alerts  
- Clean, intuitive layout for operations  

✅ Glory SOAP API Support  
- OpenOperation  
- OccupyOperation  
- ReleaseOperation  
- CloseOperation  
- GetStatus  
- ChangeOperation (Deposit / Dispense)  
- ChangeCancelOperation  
- ResetOperation  

✅ Cloud Integration
- Remote command polling from cloud API
- Automatic command execution on device
- Result code reporting back to cloud
- Configurable polling intervals
- Retry logic for network reliability  

✅ Thread‑Safe Architecture  
- 1‑second silent heartbeat (GetStatus) in a background thread  
- Deposit/Dispense operations run in worker threads  
- Cloud polling runs in background threads
- Cancel works instantly even during ChangeOperation  
- Reset supports long timeouts without freezing UI  

✅ Smart Error Handling  
- result **0** → Success  
- result **5** → Device Not Occupied (logged as warning)  
- result **11** → Invalid Request (logged as warning)
- result **21** → Invalid Session (logged as warning)  
- result **None** → Offline or timeout  
- *Note: Glory devices return many other result codes that are logged but not specifically handled*  

✅ Logging System (Color Coded)  
- 🔵 SOAP Request XML  
- 🟢 SOAP Response XML  
- 🟣 Operation results  
- 🟠 Warnings  
- 🔴 Errors  
- Logs: "⚠️ Sending request WITHOUT SessionID" when applicable  

✅ Well-Documented Code
- Comprehensive docstrings and comments
- Modular architecture with separate clients
- Easy configuration at the top of files

------------------------------------------------------------
📦 INSTALLATION
------------------------------------------------------------

Requirements:
- Python 3.10+  
- Windows 10 or newer  

Install dependencies:
    pip install -r requirements.txt

------------------------------------------------------------
▶️ RUNNING THE APPLICATION
------------------------------------------------------------

Clone the project:
    git clone https://github.com/a1364t/Glory-POS-Application.git

Navigate to folder:
    cd Glory-POS-Application

Run:
    python main.py

------------------------------------------------------------
⚙️ CONFIGURATION
------------------------------------------------------------

Edit the constants at the top of `main.py`:
- `POS_ID`: Unique identifier for this POS terminal
- `API_KEY`: Secret key for cloud API authentication
- `CLOUD_BASE_URL`: Cloud API endpoint URL
- `POLL_INTERVAL_MS`: Cloud polling frequency in milliseconds

------------------------------------------------------------
📁 PROJECT STRUCTURE
------------------------------------------------------------
```
Glory-POS-Application/
│
├── main.py                 (GUI Application)
├── bruebox_client.py       (SOAP API Client for FCC device)
├── cloud_client.py         (Cloud API Client for remote commands)
├── dist/                   (EXE build output)
├── build/                  (PyInstaller build artifacts)
├── Command.txt             (Notes / XML samples)
└── README.md               (This file)
```
------------------------------------------------------------
🏗️ BUILD EXE (OPTIONAL)
------------------------------------------------------------

Install PyInstaller:
    pip install pyinstaller

Build executable (with icon and images bundled):
    pyinstaller --onefile --windowed --icon=Images/Designer.ico --add-data "Images;Images" main.py

EXE output:
    dist/main.exe

------------------------------------------------------------
🧪 TESTING CHECKLIST
------------------------------------------------------------

✅ Session → Occupy → Deposit → Cancel → Release  
✅ Cancel during deposit works instantly  
✅ Reset works after errors  
✅ Heartbeat updates circle every second  
✅ Offline/online detection works  
✅ Cloud polling receives and executes commands  
✅ Cloud result reporting works reliably  


------------------------------------------------------------
� RELATED PROJECTS
------------------------------------------------------------

**Cloud Backend API**: The Django-based cloud service for remote POS management is available at:
[Glory Cloud API](https://github.com/a1364t/glory-cloud-api)

This provides the REST API that enables remote command execution, result tracking, and POS monitoring.

