# AutoTriage

AutoTriage is a digital forensics triage platform for collecting incident response artifacts from Windows and Linux hosts. The repository contains a web application for managing inventories and triage jobs, Ansible playbooks for remote execution, and standalone collectors for both operating systems.

## Repository Layout

```text
.
|-- backend/          FastAPI API, database models, Ansible job runner
|-- frontend/         React + Vite web interface served by Nginx in Docker
|-- Ansible/          Playbooks and example inventory files
|-- windows-triage/   PowerShell collector for Windows targets
|-- linux-triage/     Python collector for Linux targets
`-- docker-compose.yml
```

## Features

- Upload and parse Ansible INI inventories.
- Check node reachability from the web UI.
- Create triage jobs for selected nodes and collection modules.
- Run Windows and Linux collection remotely through Ansible.
- Stream triage progress through WebSockets.
- Store job status, node status, and inventory metadata in PostgreSQL.
- Publish live job events through Redis.
- Download collected artifacts from completed jobs.
- Seed an initial admin user on backend startup.

## Components

### Web Application

- Backend: FastAPI, SQLAlchemy async, PostgreSQL, Redis, JWT authentication.
- Frontend: React, React Router, TanStack Query, Zustand, Tailwind CSS.
- API docs are available from the backend at `/docs`.
- The production frontend proxies `/api/` to the backend and `/ws/` to the triage WebSocket endpoint.

### Collectors

- `windows-triage/` collects Windows volatile data, registry hives, event logs, filesystem artifacts, user artifacts, optional memory dumps, and chain-of-custody hashes.
- `linux-triage/` collects Linux volatile data, system configuration, logs, user artifacts, filesystem metadata, optional memory dumps, and chain-of-custody hashes.

### Ansible

- `Ansible/auto-triage-web.yml` is used by the backend for web-triggered jobs.
- `Ansible/auto-triage.yml` can be run manually from an Ansible control machine.
- `Ansible/inventory` is an example mixed Windows/Linux inventory.

## Prerequisites

For the Docker-based web platform:

- Docker and Docker Compose.
- An SSH private key on the host for Ansible access to targets.
- Network access from the backend container to target hosts.
- Target hosts configured for the selected Ansible connection method.

For standalone collectors:

- Windows: PowerShell 5.1+ and Administrator privileges.
- Linux: Python 3 and root privileges for best coverage.

## Configuration

Create a `.env` file in the repository root before starting Docker Compose:

```env
POSTGRES_USER=forensics
POSTGRES_PASSWORD=change-me
POSTGRES_DB=forensics_db

SECRET_KEY=change-this-secret
ACCESS_TOKEN_EXPIRE_MINUTES=480

ADMIN_USERNAME=admin
ADMIN_PASSWORD=change-me
ADMIN_EMAIL=admin@localhost

HOST_ANSIBLE_KEY_PATH=/absolute/path/to/private/key
ANSIBLE_SSH_KEY_PATH=/root/.ssh/ansible
LINUX_ANSIBLE_USER=your-linux-user
LINUX_BECOME_PASSWORD=
ARTIFACTS_DIR=/app/artifacts
```

`docker-compose.yml` runs PostgreSQL, Redis, the backend, and the frontend with host networking. The frontend listens on port `80`, and the backend listens on port `8000`.

## Running the Web Platform

Build and start the stack:

```bash
docker compose up --build
```

Open the frontend:

```text
http://localhost/
```

Log in with `ADMIN_USERNAME` and `ADMIN_PASSWORD` from `.env`.

Backend API documentation:

```text
http://localhost:8000/docs
```

## Web Workflow

1. Log in to the web UI.
2. Upload an Ansible INI inventory from the Inventories page.
3. Open the inventory and run a node status check.
4. Create a triage job, choose target nodes, and select collection modules.
5. Start the job and monitor per-node progress in real time.
6. Download generated artifacts from the completed job detail page.

Uploaded inventories support host lines such as:

```ini
[windows_nodes]
dc ansible_host=192.0.2.10 ansible_user=Administrator ansible_connection=ssh ansible_shell_type=cmd

[linux_nodes]
ubuntu-server ansible_host=192.0.2.20 ansible_user=ubuntu ansible_connection=ssh
```

Groups whose names include `linux` are treated as Linux targets by the backend runner. Other groups are treated as Windows targets.

## Artifact Storage

Web-triggered job artifacts are stored under the backend artifact directory:

```text
/app/artifacts/<job_id>/
```

With Docker Compose, this path is backed by the `artifacts_data` Docker volume. Each job directory contains generated per-job collector configuration files, a dynamic Ansible inventory, fetched collector archives, and execution logs.

## Standalone Collector Usage

### Windows

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

Optional tools can be placed in `windows-triage/Tools/`, including `DumpIt.exe` for memory acquisition and `RawCopy.exe` for locked-file collection.

### Linux

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

## Manual Ansible Usage

Edit `Ansible/inventory`, then run:

```bash
cd Ansible
ansible-playbook -i inventory auto-triage.yml
```

Manual playbook artifacts are fetched to:

```text
Ansible/fetched_artifacts/
```

## Development

Backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Set `VITE_API_URL` if the frontend development server should call a backend URL other than `/api`.

## Security Notes

- Use AutoTriage only on systems where you have authorization to collect forensic data.
- Collected artifacts can contain credentials, personal data, logs, memory contents, and other sensitive information.
- Protect SSH keys, `.env` secrets, artifact volumes, and downloaded evidence.
- Avoid plaintext production credentials in inventories; use a dedicated key, vault, or external secret management where possible.
- Windows and Linux collectors require elevated privileges for full coverage.
