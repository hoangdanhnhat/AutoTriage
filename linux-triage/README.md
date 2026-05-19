# Linux Triage Collector

Python implementation of the AutoTriage collector for Linux hosts. It mirrors the Windows collector flow: preflight checks, volatile data first, system/user/filesystem artifacts, chain-of-custody hashes, and optional ZIP packaging.

## Usage

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

## Output

Collections are written to `linux-triage/output/<timestamp>_<hostname>/` and include:

- `processes.csv` and `processes.json`
- network state under `volatile/` and `/proc/net` snapshots under `proc/net/`
- system configuration under `System/`
- log artifacts under `Logs/`
- user shell, SSH, browser, and desktop artifacts under `Users/`
- filesystem metadata under `Filesystem/`
- `ChainOfCustody.json` with hashes, sizes, timestamps, system metadata, and collection metadata
- a ZIP archive when compression is enabled

## Memory Collection

Memory collection is disabled by default in `core/config.py`. To enable it, place an executable `avml` or `lime` binary in `linux-triage/tools/` and set `collect_memory` to `True`.

