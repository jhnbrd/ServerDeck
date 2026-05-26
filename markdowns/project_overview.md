# ServerDeck: Ultimate Home Server Management Suite
## Technical Specification & Project Overview Documentation

---

## 1. Project Overview & Objectives

### 1.1 Project Name
ServerDeck

### 1.2 System Description
ServerDeck is an accessible, lightweight, asynchronous GUI process manager designed for Windows-based local development environments and home servers. It consolidates diverse application stacks (Python/Uvicorn, Node.js/NPM, .NET, PHP/Artisan) into a clean, modern, intuitive dashboard. The application replicates the simple, centralized control model of classic utilities like XAMPP, but updates it with built-in IDE integration, proactive port conflict management, user-configurable network configuration, real-time log isolation, and a non-destructive project archiving system.

### 1.3 Target Audience & Use Case
Built for full-stack developers, system administrators, and home-lab enthusiasts running multi-tiered local web services. It provides a highly visual, easy-to-read control panel that removes the need to manually manage multiple background terminal windows.

### 1.4 Core Objectives
* Streamlined Process Management: Replace scattered, manual command-line execution with an organized, thread-safe dashboard interface.
* Proactive Status Monitoring: Guarantee system predictability by auditing network interfaces and port allocations before an app launches, preventing silent startup failures.
* Modern, Clean Usability: Move away from cluttered terminal windows toward a high-contrast, minimalist, light/dark responsive GUI designed for clarity at a glance.
* Safe Configuration Management: Provide foolproof workflows for adding, modifying, hot-linking, and retiring server applications.

---

## 2. System Architecture & Lifecycle

ServerDeck functions using an asynchronous, decoupled core architecture. The user interface remains responsive at all times by delegating application processes to hidden, managed background sub-shells.

### 2.1 The Application Lifecycle
1. System Discovery Initialization: ServerDeck starts, automatically identifies active network adapters, and populates the network interface panel with the current configuration.
2. Dashboard Assembly: The app reads the local projects.json structure, programmatically building a clean, uniform list view of user applications.
3. Pre-Flight Port Validation: The internal socket engine safely tests the requested ports, setting row badges to a descriptive state: Ready, Active, or Port Conflict.
4. Isolated Sub-Shell Execution: Clicking Start provisions a non-blocking operating system worker. The process runs quietly in the background while caching its system Process ID (PID) and linking its communication output directly to the UI.
5. Continuous Heartbeat Monitoring: A background timer runs every 1000ms to check the exact status of the PIDs. If an application crashes or closes externally, the dashboard instantly refreshes its status to keep the user informed.

---

## 3. Comprehensive Feature Set

### 3.1 Clean Global Control Center
* Interactive IP Setup Panel: Clear text inputs allow users to safely specify their preferred Local IP, Subnet Mask, and Gateway. Clicking "Apply Network Configuration" smoothly updates the server's hardware settings using an automated system execution format:  
  netsh interface ip set address name="[ADAPTER_NAME]" static [USER_IP] [USER_SUBNET] [USER_GATEWAY]  
  The system provides plain-language popups if the tool lacks the required Windows Administrator permissions to apply network changes.
* One-Click Start All: Safely loops through every entry in the user's project file, validating network ports sequentially before initiating full stack execution.
* Global Stop All Switch: Instantly checks the internal dictionary of running processes and safely terminates all active background environments simultaneously.

### 3.2 Granular Project Components (The Clean List View)
Every application card inside the primary interface grid uses standard design elements to manage a project's state:

* Start / Stop Toggle: A prominent button that dynamically switches function based on the process state. It handles system environment path variables and directory mapping smoothly behind the scenes.
* View Console Window: Opens a tailored, separate diagnostic window displaying only the text output of that specific application. This handles standard output (stdout) and standard error (stderr) streams cleanly, allowing users to review initialization messages, framework errors, or database warnings without any terminal clutter.
* Open Directory: Launches a native, clean Windows File Explorer window directly inside the project's root workspace directory.
* Open in VS Code: Launches the user's preferred code editor (VS Code) directly inside the project root via an asynchronous execution shortcut (code .).
* Move to Archive: Safe, non-destructive removal. It shifts the project entry out of the active dashboard panel into an archived layer within projects.json. This keeps the main view clean while ensuring your custom run arguments and paths are never permanently deleted.

### 3.3 Guided Project Wizard (Creation & Editing Modal)
A user-friendly form interface designed to prevent entry errors:
* Friendly Naming Inputs: Standard text inputs for clean display names.
* Visual Asset Assigner: An intuitive file picker to link a customized application logo (.png/.ico), making items instantly recognizable in the main menu list.
* Directory Path Picker: A standard file browser interface (filedialog.askdirectory()) to safely set the exact execution directory.
* Smart Port Configuration Field: An input box tied directly to the live network socket auditor. If a user types in a port numbers that is already taken by Windows or another app, the field alerts them immediately before they click save.
* Launch Argument Field: A clear text area to save execution instructions (e.g., npm run dev or python -m uvicorn main:app --host 0.0.0.0), keeping startup options visible and fully editable.

---

## 4. Technical Architecture & Data Management

### 4.1 Reliable Flat-File Storage (projects.json)
Application definitions use a simple, lightweight JSON file. This design avoids heavy runtime engine installations or external local database drivers.

The database is divided into two structural node arrays: active_projects and archived_projects. Each record maps explicit configuration elements including names, paths, assigned ports, visual iconography asset keys, raw execution strings, and tracking states.

---

## 5. UI/UX Design, Footprint, & Color Palette Guide

### 5.1 Compact Window Geometry (The XAMPP Footprint)
To prevent the application from taking over the user's desktop, the GUI enforces a strict, compact layout strategy modeled directly after the XAMPP Control Panel:
* Window Bounds: Hardcoded starting size set to exactly 680 pixels wide by 450 pixels high.
* Resizing Constraints: Window resizing is strictly disabled or locked to a tight maximum parameter. This ensures that elements stay perfectly arranged and the app remains a small, unobtrusive utility widget in the corner of your screen.
* Modals & Popups: Sub-windows (Add Project Wizard and Console Logs Window) open as independent, lightweight overlay panels that adapt to the same compact dimensions.

### 5.2 The Strategic Color Palette
Using CustomTkinter, you can define a native light/dark theme using soft, accessible color tokens instead of harsh pure blacks and bright neon greens:

* Primary Background (Dark Mode): #1A1D20 (Deep, elegant slate grey)
* Card/Container Background: #24292E (Slightly lighter charcoal grey to create elevation)
* Accent/Primary Buttons: #0066CC or #2F855A (Corporate blue or soft forest green)
* Text Component: #E1E4E8 (Off-white/light grey for high readability)

#### Dynamic Status Component Badges
* Active/Running State: Soft Mint Green background (#DEF7EC) with Deep Sage text (#03543F).
* Standby/Ready State: Soft Neutral Grey background (#F3F4F6) with Charcoal text (#374151).
* Conflict/Error State: Soft Pastel Red background (#FDE8E8) with Crimson text (#9B1C1C).

### 5.3 Layout Architecture & Component Blueprint
* Clean Structural Containers: Each project sits inside a distinct, rounded card block (radius=8) with generous inner padding. This separates your data naturally without resorting to dense horizontal separator grid lines.
* Icon Integration: Mapped logos (Python, Node, .NET) are rendered inside small circular frames with soft background shading to give each project an easily recognizable visual anchor.
* The Clean Context Menu: To optimize horizontal real estate and maximize whitespace, immediate row actions are limited to "Start/Stop" and "Console". Less frequent actions (Open Directory, Open in VS Code, Move to Archive) are safely stored inside a professional drop-down utility menu icon [...] at the right margin of each row.

---

## 6. Project Roadmap & Delivery Phases

### Phase 1: Asynchronous Core Engine (Weeks 1–2)
### Phase 2: Interface Design & Local File Linking (Weeks 3–4)
### Phase 3: Automation & System Integration (Weeks 5–6)

---

## 7. Conclusion
ServerDeck turns home server management from a messy collection of command prompt boxes into a clean, centralized workspace dashboard.