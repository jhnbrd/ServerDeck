# ServerDeck

A lightweight, open-source control panel for managing local development servers on Windows. ServerDeck gives you a compact dashboard—similar in spirit to XAMPP or Docker Desktop—for starting, stopping, and monitoring your home-lab and full-stack projects without juggling multiple terminal windows.

## Features

- **Compact dashboard** — Fixed utility window with a clean dark UI
- **Per-project control** — Start, stop, view console output, open directory, launch VS Code
- **Port conflict detection** — Pre-flight socket checks before launching services
- **Process tree teardown** — Safely terminates child processes (npm, Vite, etc.) on stop
- **Network configuration** — Set static IP, subnet, gateway, and adapter via `netsh`
- **Buffered console logs** — Output is captured from the moment a project starts, even before you open its console
- **SQLite storage** — Projects stored locally in `serverdeck.db` (auto-created, gitignored)
- **Non-destructive archive** — Retire projects without deleting their configuration

## Minimum requirements

### ServerDeck itself

| Requirement | Minimum |
|---|---|
| **OS** | Windows 10 or later (64-bit) |
| **Python** | 3.10 or later |
| **RAM** | 512 MB free (1 GB+ recommended if running many services) |
| **Disk** | ~50 MB for ServerDeck + dependencies |
| **Display** | 680×520 minimum window size |
| **Admin rights** | Required only when applying network settings (`netsh`) |

### Python dependencies

Installed automatically via `pip install -r requirements.txt`:

- `customtkinter` 5.2+
- `psutil` 5.9+
- `Pillow` 10.2+

### Your projects (not bundled)

ServerDeck does **not** ship Node, .NET, PHP, Python venvs, or your app code. Each application you register must already be installed and runnable on that machine. Examples:

| Stack | You need on the PC |
|---|---|
| Python / FastAPI | Python venv, dependencies, valid `uvicorn` command |
| Node / React / Vite | Node.js, `npm install` done in project folder |
| .NET | .NET SDK matching the project |
| PHP / Laravel | PHP, Composer, project dependencies |

## Installation

```powershell
git clone https://github.com/your-org/ServerDeck.git
cd ServerDeck
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

On first launch, ServerDeck creates an empty `serverdeck.db` in the project root. No sample projects are bundled—you add your own through the UI, or optionally use a local seeder (see below).

### Optional: local project seeder

For a personal dev setup, copy the example seeder and customize it with your machine paths:

```powershell
copy seed_local.example.py seed_local.py
python seed_local.py
```

`seed_local.py` is gitignored so your paths stay local. Use `--force` to archive existing projects and re-seed:

```powershell
python seed_local.py --force
```

## How to use

### 1. Launch ServerDeck

```powershell
cd ServerDeck
venv\Scripts\activate
python main.py
```

On startup, ServerDeck will automatically:

1. **Apply network settings** from the Network panel (adapter, IP, subnet, gateway)
2. **Start all configured applications** that are not already running

These run in the background; progress appears in **System Status Logs** at the bottom of the window.

> **Note:** Applying network settings requires administrator privileges. Run ServerDeck as admin if you use static IP configuration, or ignore network warnings if you only need process management.

### 2. Network panel (top)

| Field | Purpose |
|---|---|
| **IP / Subnet / Gateway** | Static network values to apply |
| **Adapter** | Which network interface to configure |
| **✓ Apply Network** | Manually push settings via `netsh` |

On launch, the panel is pre-filled from your current adapter. Values are applied automatically; use **Apply Network** only if you changed something manually.

### 3. Toolbar

| Button | What it does |
|---|---|
| **▶ Start All** | Starts every configured application that is not running |
| **■ Stop All** | Stops all tracked apps and frees their ports (including orphaned processes from a previous session) |
| **+ Add New Application** | Opens the project wizard |
| **Running counter** | Shows `running / total` apps |

### 4. Application rows

Each row shows the app name, port, status badge, and actions:

| Control | What it does |
|---|---|
| **Start / Stop** | Toggle that single application |
| **>_ Console** | Open a live log window (includes output from before you opened it) |
| **••• menu** | Open directory, open in VS Code, edit settings, or archive |

**Status badges:**

| Badge | Meaning |
|---|---|
| **● Ready** | Port is free; safe to start |
| **● Active** | ServerDeck is running this app |
| **● Conflict** | Port is already in use by something else — click **Fix** to edit the port, or use **Stop All** |

### 5. System Status Logs

The log panel at the bottom shows ServerDeck events: starts, stops, port audits, and network results. Scroll to review history; use **Clear** to wipe the display.

### 6. Closing ServerDeck

When you close the window with **X**, ServerDeck stops **all configured applications** before exiting. Always use the window close button rather than killing Python from Task Manager, or orphaned processes may keep holding ports.

If ports still show **Conflict** after a crash or force-kill, click **Stop All** on the next launch.

### 7. Run at Windows login (optional)

Create a local startup script (not committed to git). Example `start_serverdeck.bat`:

```bat
@echo off
if /I not "%~1"=="hidden" (
    mshta "javascript:var sh=new ActiveXObject('WScript.Shell'); sh.Run('\"\"\"%~f0\"\"\" hidden', 0); close()"
    exit /b
)

cd /d D:\Projects\ServerDeck
pythonw main.py
```

1. Update `cd /d` to your ServerDeck folder
2. Use the full path to `pythonw.exe` if Python is not on PATH at login:
   ```bat
   "C:\Path\To\Python\pythonw.exe" main.py
   ```
3. Copy the `.bat` into the Startup folder: press **Win + R**, type `shell:startup`, press Enter

The hidden launcher avoids a flashing CMD window. ServerDeck will auto-apply network settings and start all apps when you log in.

## Adding your first application

1. Launch ServerDeck
2. Click **+ Add New Application**
3. Fill in:
   - **Display Name** — Label shown in the dashboard
   - **Project Directory** — Working directory for the process
   - **Port** — TCP port the service listens on (validated live)
   - **Launch Command** — Shell command to start the service
   - **Icon** *(optional)* — `.png` or `.ico` for the row

### Example commands

| Stack | Example launch command |
|-------|------------------------|
| Python / Uvicorn | `call venv\Scripts\activate && uvicorn main:app --host 0.0.0.0 --port 8000` |
| Node / npm | `set PORT=3000 && npm run dev` |
| .NET | `dotnet run --urls=http://0.0.0.0:5000` |
| PHP / Laravel | `php artisan serve --host=0.0.0.0 --port=8080` |

**Tips:**

- Use `0.0.0.0` as the host so the service is reachable on your LAN, not just `localhost`
- Match the port in your launch command to the **Port** field in ServerDeck
- Use `&&` to chain steps (activate venv, set env vars, then run)

## Project structure

```
ServerDeck/
├── main.py              # Entry point
├── core/                # Process manager, port checker, network, database
├── ui/                  # CustomTkinter dashboard and modals
├── requirements.txt
└── serverdeck.db        # Created at runtime (not committed)
```

## Contributing

Contributions are welcome. Please open an issue to discuss significant changes before submitting a pull request.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-change`)
3. Commit your changes
4. Open a pull request

## License

This project is licensed under the [MIT License](LICENSE).
