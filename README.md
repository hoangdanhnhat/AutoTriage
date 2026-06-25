# AutoTriage

AutoTriage is a digital forensics triage platform for collecting incident response artifacts from Windows and Linux hosts. It combines a web application, a FastAPI backend, Ansible-based remote execution, and standalone collectors for operating system artifact collection.

The project is designed for authorized incident response workflows where an operator needs to upload target inventories, verify node reachability, launch focused collection jobs, monitor progress live, and download collected evidence artifacts.

## Features

- Web dashboard for managing inventories, target nodes, and triage jobs.
- Ansible INI inventory upload and parsing.
- Node reachability checks from the web UI.
- Windows and Linux triage job creation with selectable collection modules.
- Real-time job and node progress through WebSockets.
- PostgreSQL-backed job, inventory, node, and user storage.
- Redis pub/sub for live job event delivery.
- Remote execution through Ansible playbooks.
- Artifact download for completed or partially completed jobs.
- Standalone Windows PowerShell collector.
- Standalone Linux Python collector.
- First-run admin user seeding from environment variables.

## Repository Layout

```text
.
|-- backend/          FastAPI API, database models, auth, WebSockets, Ansible job runner
|-- frontend/         React + Vite application served by Nginx in Docker
|-- Ansible/          Web and manual Ansible playbooks plus sample inventory files
|-- windows-triage/   PowerShell collector for Windows targets
|-- linux-triage/     Python collector for Linux targets
`-- docker-compose.yml Docker Compose stack for the web platform
```

## Architecture

```text
Browser
  |
  | HTTP / WebSocket
  v
Frontend (React + Nginx)
  |
  | /api and /ws proxy
  v
Backend (FastAPI)
  |        |
  |        | stores app data
  |        v
  |      PostgreSQL
  |
  | publishes live job events
  v
Redis
  |
  | runs ansible-playbook
  v
Ansible control process
  |
  | copies collectors and fetches artifacts
  v
Windows / Linux target hosts
```

## Tech Stack

- **Frontend:** React, Vite, React Router, TanStack Query, Zustand, Tailwind CSS, Lucide icons.
- **Backend:** FastAPI, SQLAlchemy async, PostgreSQL, Redis, JWT authentication.
- **Automation:** Ansible Core with Windows collection support.
- **Collectors:** PowerShell for Windows, Python for Linux.
- **Runtime:** Docker Compose for the web platform.

## Collection Modules

### Windows

- Volatile data: processes, network connections, and system state.
- Registry hives: SAM, SECURITY, SOFTWARE, SYSTEM, and user NTUSER files.
- Event logs: Windows `.evtx` files.
- Windows artifacts: AppCompat, scheduled tasks, services, and related system artifacts.
- User artifacts: browser history, recent files, shell history, and PowerShell history.
- ProgramData: startup items, Windows Error Reporting, Defender, and application logs.
- Optional NTFS artifacts: MFT collection with `RawCopy.exe`.
- Optional Prefetch files.
- Optional memory dump with a supported memory tool.

### Linux

- Volatile data: processes, network connections, and system state.
- System artifacts: OS release, users, services, cron, mounts, and packages.
- Log artifacts from common system and application log paths.
- User artifacts: shell history, SSH files, and desktop user traces.
- Filesystem artifacts: SUID files, world-writable paths, temp files, and recently changed files.
- Optional memory dump with AVML or LiME when available.

## Prerequisites

For the Docker-based web platform:

- Docker and Docker Compose.
- An SSH private key on the host for Ansible access to target systems.
- Network access from the backend container to target hosts.
- Target hosts configured for the expected Ansible connection method.
- Administrator/root privileges on targets when full artifact coverage is required.

For standalone collectors:

- Windows: PowerShell 5.1 or newer, ideally running as Administrator.
- Linux: Python 3, ideally running as root.

## Configuration

Copy the example environment file:

```bash
cp .env.example .env
```

Then edit `.env` and set real values:

```env
POSTGRES_USER=forensics
POSTGRES_PASSWORD=changeme_strong_password
POSTGRES_DB=forensics_db
DATABASE_URL=postgresql+asyncpg://forensics:changeme_strong_password@db:5432/forensics_db

REDIS_URL=redis://redis:6379/0

SECRET_KEY=changeme_generate_a_real_secret_key
ACCESS_TOKEN_EXPIRE_MINUTES=480

ANSIBLE_SSH_KEY_PATH=/root/.ssh/ansible
HOST_ANSIBLE_KEY_PATH=/absolute/path/to/private/key
LINUX_ANSIBLE_USER=ubuntu
LINUX_BECOME_PASSWORD=

ARTIFACTS_DIR=/app/artifacts

ADMIN_USERNAME=admin
ADMIN_PASSWORD=changeme_admin_password
ADMIN_EMAIL=admin@localhost
```

Generate a strong `SECRET_KEY` with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

`HOST_ANSIBLE_KEY_PATH` is the private key path on your host machine. Docker Compose mounts it into the backend container at `ANSIBLE_SSH_KEY_PATH`.

## Running the Web Platform

Build and start the full stack:

```bash
docker compose up --build
```

Open the web UI:

```text
http://localhost/
```

Open the backend API docs:

```text
http://localhost:8000/docs
```

Log in with the admin account configured in `.env`.

## Web Workflow

1. Log in to the web UI.
2. Upload an Ansible INI inventory from the Inventories page.
3. Open the inventory or dashboard and run a node status check.
4. Create a new triage job.
5. Select target nodes.
6. Select the Windows and Linux collection modules needed for the case.
7. Start the job.
8. Monitor node progress and live logs in the job detail page.
9. Download collected artifacts after the job completes.

## Inventory Format

AutoTriage accepts Ansible INI-style inventories. Groups whose names include `linux` are treated as Linux targets; other groups are treated as Windows targets.

Example:

```ini
[windows_nodes]
dc01 ansible_host=192.0.2.10 ansible_user=Administrator ansible_connection=ssh ansible_shell_type=cmd

[linux_nodes]
ubuntu01 ansible_host=192.0.2.20 ansible_user=ubuntu ansible_connection=ssh
```

Group variables are also supported:

```ini
[linux_nodes:vars]
ansible_user=ubuntu
ansible_connection=ssh
```

## Artifact Storage

Web-triggered job artifacts are stored inside the backend container under:

```text
/app/artifacts/<job_id>/
```

With Docker Compose, this path is backed by the `artifacts_data` Docker volume. Each job directory can contain:

- Generated job-specific collector configuration files.
- Dynamic Ansible inventory.
- Fetched Windows ZIP artifacts.
- Fetched Linux ZIP, TAR, or TAR.GZ artifacts.
- Per-host execution logs.

## Manual Ansible Usage

You can also run the Ansible playbook manually from an Ansible control machine:

```bash
cd Ansible
ansible-playbook -i inventory auto-triage.yml
```

Manual playbook artifacts are fetched to:

```text
Ansible/fetched_artifacts/
```

The web application uses:

```text
Ansible/auto-triage-web.yml
```

## Standalone Collector Usage

### Windows Collector

Run PowerShell as Administrator:

```powershell
cd windows-triage
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
.\Core\MainCollector.ps1
```

Common options:

```powershell
.\Core\MainCollector.ps1 -SkipMemory
.\Core\MainCollector.ps1 -OutputLocation "D:\Evidence"
.\Core\MainCollector.ps1 -QuickMode
```

Optional tools can be placed in `windows-triage/Tools/`, including:

- `DumpIt.exe` for memory acquisition.
- `RawCopy.exe` for locked-file and NTFS artifact collection.

### Linux Collector

Run as root for best coverage:

```bash
sudo python3 linux-triage/main.py
```

Common options:

```bash
sudo python3 linux-triage/main.py --quick-mode
sudo python3 linux-triage/main.py --skip-memory
sudo python3 linux-triage/main.py --output-location /mnt/evidence
sudo python3 linux-triage/main.py --no-compress
```

Linux memory collection is disabled by default. To enable it, place an executable `avml` or `lime` binary in `linux-triage/tools/` and enable memory collection in `linux-triage/core/config.py` or through the web job module selection.

## Local Development

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

On Windows PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Set `VITE_API_URL` if the frontend development server should call a backend URL other than `/api`.

Set `VITE_WS_URL` if WebSocket traffic should use a custom endpoint.

## API Overview

The backend exposes API documentation at:

```text
http://localhost:8000/docs
```

Main API areas:

- `/auth` for login and current-user lookup.
- `/inventories` for inventory upload, listing, detail, deletion, and node retrieval.
- `/inventories/{id}/check-status` for node reachability checks.
- `/triage/jobs` for job creation, listing, detail, and execution.
- `/triage/jobs/{id}/artifacts` for artifact listing and downloads.
- `/ws/triage/{job_id}` for live job updates.

## Security Notes

- Use AutoTriage only on systems where you have explicit authorization to collect forensic data.
- Collected artifacts may contain credentials, personal information, logs, memory contents, and other sensitive evidence.
- Protect `.env`, SSH keys, artifact volumes, downloaded evidence, and database backups.
- Replace all default passwords and secrets before running outside a local lab.
- Avoid plaintext production credentials in inventories. Prefer dedicated keys, vaulting, or external secret management.
- Limit access to the web UI and backend API to trusted operators and networks.
- Run collectors with elevated privileges only when appropriate for the engagement.

## Troubleshooting

### Backend cannot connect to targets

- Confirm the backend container can reach the target network.
- Confirm `HOST_ANSIBLE_KEY_PATH` points to a readable private key.
- Confirm the target host accepts the configured Ansible user and connection method.
- Check target firewalls and SSH/WinRM configuration.

### No artifacts are returned

- Open the job detail page and review per-node logs.
- Check the backend artifact volume.
- Confirm the selected modules are supported on the target OS.
- Confirm the collector has permission to read the requested artifact paths.

### WebSocket updates do not appear

- Confirm Redis is healthy.
- Confirm `/ws/` is proxied by Nginx.
- Confirm the browser is authenticated with a valid token.

## Project Status

AutoTriage is an active forensics and incident response project. The current implementation is suitable for lab use and controlled environments. Before production use, consider adding stricter secret validation, durable background workers, database migrations, role-based access control, and automated tests.
