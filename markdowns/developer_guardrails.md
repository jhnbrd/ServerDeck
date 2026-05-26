# ServerDeck: Guardrails & Critical Implementation Instructions
## Crucial Technical Parameters to Prevent Code Failure

---

## 1. Process Management Engine Guardrails (MANDATORY)

### 1.1 Recursive Tree Process Termination (Crucial!)
* **The Danger:** When triggering commands like `npm run dev` or `php artisan serve`, the target platform acts as a shell multiplexer, spinning up independent sub-worker nodes (like Vite, Webpack, or native compiler loops). Directly terminating the core parent shell process ID leaves these sub-workers orphaned and running silently, causing permanent network port blockages.
* **The Architectural Fix:** The process manager must implement an explicit, multi-layered breakdown algorithm rather than a single process termination call:
  1. Instantiate a system process tracking object mapped directly to the active parent process identifier (PID).
  2. Query the operating system to retrieve a complete array of all child and sub-worker processes spawned under that parent, explicitly enabling deep recursive scanning.
  3. Loop through the collected sub-worker array from the bottom up, issuing a termination or kill signal to each individual child node first.
  4. Once child background tasks are fully dismantled, execute the final termination signal on the root parent shell process.
  5. Enclose the entire teardown pipeline within an exception wrapper to safely catch instances where a process or worker has already exited naturally, preventing unexpected system crashes.

### 1.2 Non-Blocking Asynchronous Process Execution
* Do NOT run process spawns directly inside the main UI loop sequence. This freezes the dashboard and throws thread deadlocks.
* All background applications must be provisioned utilizing decoupled, non-blocking asynchronous wrappers. Standard output (stdout) and standard error (stderr) data streams must be funneled directly to isolated background listener tasks to ensure the main interface remains entirely fluid and responsive.

---

## 2. Network Interface & Socket Diagnostics

### 2.1 Live Port Verification Engine
* Before launching any background process, the engine must execute a preemptive network socket query to verify that the requested port is vacant.
* **The Diagnostic Logic Workflow:**
  1. Initialize a low-latency network socket configuration set to IPv4 streaming behavior.
  2. Direct a probing connection handshake sequence strictly toward the standard local loopback address (`127.0.0.1`) using the target application's port number.
  3. Intercept the returned integer response code from the connection attempt.
  4. If the socket routine catches a successful handshake return state (an explicit exit code of `0`), the architecture must interpret this as an occupied port, blocking execution and changing the row badge state directly to `Conflict`.
  5. Wrap the initialization in an auto-disposing context boundary to guarantee the probe socket closes instantly and drops its network handles immediately after the test completes.

### 2.2 Elevated Sub-Shell System Privileges
* Applying network static configurations using `netsh` requires elevated Windows Administrator permissions. 
* Code must wrap the network operation in structural error handlers. If an Access Denied or privilege exception is caught, it must cleanly log a plain-language error explaining how to resolve it ("Please launch ServerDeck as Administrator") instead of crashing.

---

## 3. Data Integrity & File Configurations

### 3.1 Serialization Stability (`projects.json`)
* The configuration structure must maintain absolute consistency. Missing keys or null fields inside a row data object should default cleanly rather than causing dashboard rendering errors.
* Provide an internal fallback check when initializing structural arrays (`active_projects`, `archived_projects`).

### 3.2 Non-Destructive Archiving Structure
* Clicking the "Archive" action button must pop the object entry array directly out of the `active_projects` node sequence and append it safely inside the `archived_projects` array within `projects.json`. Under no circumstances should database deletion methods wipe rows permanently unless explicitly directed.

---

## 4. UI/UX Constraint Layout Guardrails

### 4.1 Strict Geometry Restrictions (The Footprint Rule)
* The window configuration layout template must be fixed to a compact desktop utility footprint. 
* Enforce layout metrics using hardcoded application window parameters:
  * Force base dimensions to exactly 680 pixels wide by 450 pixels high.
  * Explicitly disable user-facing horizontal and vertical window resizing behavior.
* Layout frameworks must scale gracefully. Spacing, typography margins, and status containers must prevent clipped text artifacts.

### 4.2 Streamed "See Console" Log Windows
* Each project console panel layout must run on an isolated, decoupled text reader task.
* The streaming text boxes must read incoming line data incrementally without filling system memory buffers or locking the graphic rendering thread loop.
* Provide interactive clear methods, search queries, and auto-scroll freeze parameters directly within the independent frame view.