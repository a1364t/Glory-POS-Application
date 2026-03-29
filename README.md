# Glory POS Application

A custom Point‑of‑Sale (POS) controller application built in **Python** using **PyQt5**, designed to communicate with **Glory BrueBox / CDM 9(Cash Deposit Module)/ ADM (Automatic Deposit Machine)** devices via SOAP.
The application provides a clean UI to manage sessions, deposits, dispensing, status checks, resets, and transaction cancellations — all without freezing the interface.

------------------------------------------------------------
🚀 FEATURES
------------------------------------------------------------

✅ Modern PyQt5 POS Interface  
- Live connection indicator (Online / Offline / Error)  
- Status header with color-coded alerts  
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
- 1‑second silent heartbeat (GetStatus) in a background thread  
- Deposit/Dispense operations run in worker threads  
- Cancel works instantly even during ChangeOperation  
- Reset supports long timeouts without freezing UI  

✅ Smart Error Handling  
- result **0** → Success  
- result **5** → Device Not Occupied (logged as warning)  
- result **21** → Invalid Session (logged clearly)  
- result **None** → Offline or timeout  

✅ Logging System (Color Coded)  
- 🔵 SOAP Request XML  
- 🟢 SOAP Response XML  
- 🟣 Operation results  
- 🟠 Warnings  
- 🔴 Errors  
- Logs: “⚠️ Sending request WITHOUT SessionID” when applicable  

------------------------------------------------------------
📦 INSTALLATION
------------------------------------------------------------

Requirements:
- Python 3.10+  
- Windows 10 or newer  

Install dependencies:
    pip install PyQt5 requests

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
📁 PROJECT STRUCTURE
------------------------------------------------------------

Glory-POS-Application/
|
+-- main.py                 (GUI Application)
+-- bruebox_client.py       (SOAP API Client)
+-- dist/                   (EXE build output)
+-- build/                  (PyInstaller build artifacts)
+-- Command.txt             (Notes / XML samples)
+-- README.md               (This file)

------------------------------------------------------------
🏗️ BUILD EXE (OPTIONAL)
------------------------------------------------------------

Install PyInstaller:
    pip install pyinstaller

Build executable:
    pyinstaller --onefile --windowed main.py

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

------------------------------------------------------------
📌 FUTURE IMPROVEMENTS (OPTIONAL)
------------------------------------------------------------

- Live cassette inventory dashboard   
- Auto‑save logs to file   
- Enhanced diagnostics panel  

------------------------------------------------------------
👤 AUTHOR
------------------------------------------------------------

**Alireza Talaei**  
Infrastructure Project Engineer  
Sydney, Australia  

------------------------------------------------------------
🔒 LICENSE
------------------------------------------------------------

This project is private and intended for internal development and integration testing.

