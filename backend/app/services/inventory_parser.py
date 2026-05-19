"""
Parse Ansible INI-format inventory files into structured node dicts.

Supported INI conventions:
  [group_name]
  host_alias ansible_host=IP key=value ...
  bare_ip_or_hostname key=value ...

  [group_name:vars]
  ansible_user=...
  ansible_connection=...
  ansible_shell_type=...
"""
import re
from typing import Any


def _parse_vars_line(line: str) -> dict[str, str]:
    """Parse 'key=value key2=value2 ...' into a dict."""
    result: dict[str, str] = {}
    for token in re.findall(r'(\w+)=("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'|\S+)', line):
        k, v = token
        # Strip surrounding quotes
        if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
            v = v[1:-1]
        result[k] = v
    return result


def parse_inventory(content: str) -> dict[str, Any]:
    """
    Returns:
        {
          "groups": {
            "group_name": {
              "vars": {"ansible_user": "...", ...},
              "nodes": [
                {
                  "ip_address": "...",
                  "hostname": "...",
                  "ansible_user": "...",
                  "ansible_connection": "ssh",
                  "ansible_shell_type": "powershell",
                  "extra_vars": {...}
                },
                ...
              ]
            }
          }
        }
    """
    groups: dict[str, dict] = {}
    current_group: str | None = None
    is_vars_block = False

    for raw_line in content.splitlines():
        line = raw_line.strip()

        # Skip empty lines and comments
        if not line or line.startswith("#") or line.startswith(";"):
            continue

        # Group header
        if line.startswith("[") and line.endswith("]"):
            header = line[1:-1]
            if header.endswith(":vars"):
                current_group = header[:-5]
                is_vars_block = True
            elif header.endswith(":children"):
                current_group = None
                is_vars_block = False
            else:
                current_group = header
                is_vars_block = False
                if current_group not in groups:
                    groups[current_group] = {"vars": {}, "nodes": []}
            continue

        if current_group is None:
            continue

        if is_vars_block:
            # key=value lines
            kv = _parse_vars_line(line)
            if current_group not in groups:
                groups[current_group] = {"vars": {}, "nodes": []}
            groups[current_group]["vars"].update(kv)
        else:
            # Host line: [alias] [key=value ...]
            parts = line.split()
            host_alias = parts[0]
            inline_vars = _parse_vars_line(" ".join(parts[1:]))

            ip_address = inline_vars.pop("ansible_host", host_alias)
            # If host_alias looks like an IP, use it as ip_address
            if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", host_alias):
                ip_address = host_alias
                host_alias_name = None
            else:
                host_alias_name = host_alias

            node: dict[str, Any] = {
                "ip_address": ip_address,
                "hostname": host_alias_name,
                "ansible_user": inline_vars.pop("ansible_user", None),
                "ansible_connection": inline_vars.pop("ansible_connection", None),
                "ansible_shell_type": inline_vars.pop("ansible_shell_type", None),
                "group_name": current_group,
                "extra_vars": inline_vars if inline_vars else {},
            }
            if current_group not in groups:
                groups[current_group] = {"vars": {}, "nodes": []}
            groups[current_group]["nodes"].append(node)

    # Merge group-level vars into each node (node inline vars take precedence)
    for group_data in groups.values():
        gvars = group_data.get("vars", {})
        for node in group_data.get("nodes", []):
            if node["ansible_user"] is None:
                node["ansible_user"] = gvars.get("ansible_user")
            if node["ansible_connection"] is None:
                node["ansible_connection"] = gvars.get("ansible_connection", "ssh")
            if node["ansible_shell_type"] is None:
                node["ansible_shell_type"] = gvars.get("ansible_shell_type", "powershell")

    return {"groups": groups}


def flatten_nodes(parsed: dict[str, Any]) -> list[dict[str, Any]]:
    """Return a flat list of node dicts across all groups (deduplicated by ip_address)."""
    seen_ips: set[str] = set()
    nodes: list[dict[str, Any]] = []
    for group_data in parsed.get("groups", {}).values():
        for n in group_data.get("nodes", []):
            if n["ip_address"] not in seen_ips:
                seen_ips.add(n["ip_address"])
                nodes.append(n)
    return nodes
