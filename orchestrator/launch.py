import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSPACES = ROOT / "workspaces"


def read_text(path: Path) -> str:
    return path.read_text() if path.exists() else ""


def load_workspace_context(name: str) -> dict:
    workspace = WORKSPACES / name
    shared = WORKSPACES / "_shared"
    return {
        "workspace": str(workspace),
        "base_system": bool(read_text(shared / "base-system.md")),
        "user": bool(read_text(shared / "user.md")),
        "soul": bool(read_text(workspace / "soul.md")),
        "identity": bool(read_text(workspace / "identity.md")),
        "bootstrap": bool(read_text(workspace / "BOOTSTRAP.md")),
        "memory_god": bool(read_text(workspace / "memory" / "god.md")),
        "settings": bool(read_text(workspace / "settings.json")),
        "gateway": bool(read_text(workspace / "gateway.json")),
    }


def ensure_workspace(name: str) -> Path:
    from ohmo.workspace import initialize_workspace

    workspace = WORKSPACES / name
    initialize_workspace(workspace)
    return workspace


def run_probe(name: str) -> dict:
    workspace = ensure_workspace(name)
    script = workspace / "run.py"
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
        env={**os.environ, "OHMO_WORKSPACE": str(workspace)},
    )
    return json.loads(result.stdout)


def spawn_ohmo(name: str) -> subprocess.Popen:
    workspace = ensure_workspace(name)
    env = {**os.environ, "OHMO_WORKSPACE": str(workspace)}
    return subprocess.Popen(
        [sys.executable, "-m", "ohmo", "chat", "--workspace", str(workspace)],
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ohmo", action="store_true", help="spawn real ohmo chat processes")
    args = parser.parse_args()

    router_context = load_workspace_context("router")
    marketing_context = load_workspace_context("marketing")

    payload = {
        "status": "launcher-ran",
        "contexts": {
            "router": router_context,
            "marketing": marketing_context,
        },
    }

    if args.ohmo:
        router_proc = spawn_ohmo("router")
        marketing_proc = spawn_ohmo("marketing")
        time.sleep(2)
        payload["ohmo_processes"] = {
            "router_pid": router_proc.pid,
            "marketing_pid": marketing_proc.pid,
        }
    else:
        payload["probes"] = {
            "router": run_probe("router"),
            "marketing": run_probe("marketing"),
        }

    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
