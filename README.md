# ServerDeck

A lightweight, open-source control panel for managing local development servers on Windows. ServerDeck gives you a compact dashboard—similar in spirit to XAMPP or Docker Desktop—for starting, stopping, and monitoring your home-lab and full-stack projects without juggling multiple terminal windows.

## Features

- **Compact dashboard** — Fixed 680×450 utility window with a clean dark UI
- **Per-project control** — Start, stop, view console output, open directory, launch VS Code
- **Port conflict detection** — Pre-flight socket checks before launching services
- **Process tree teardown** — Safely terminates child processes (npm, Vite, etc.) on stop
- **Network configuration** — Set static IP, subnet, gateway, and adapter via `netsh`
- **SQLite storage** — Projects stored locally in `serverdeck.db` (auto-created, gitignored)
- **Non-destructive archive** — Retire projects without deleting their configuration

## Requirements

- Windows 10 or later
- Python 3.10+
- Administrator privileges (only needed for network configuration changes)

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
