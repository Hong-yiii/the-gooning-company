from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
WORKSPACE = Path(__file__).resolve().parent
SHARED = ROOT / "workspaces" / "_shared"


def read_text(path: Path) -> str:
    return path.read_text() if path.exists() else ""


def main() -> None:
    packet = {
        "agent": "marketing",
        "workspace": str(WORKSPACE),
        "loaded": {
            "base_system": bool(read_text(SHARED / "base-system.md")),
            "user": bool(read_text(SHARED / "user.md")),
            "soul": bool(read_text(WORKSPACE / "soul.md")),
            "identity": bool(read_text(WORKSPACE / "identity.md")),
            "bootstrap": bool(read_text(WORKSPACE / "BOOTSTRAP.md")),
            "memory_god": bool(read_text(WORKSPACE / "memory" / "god.md")),
        },
        "status": "marketing-process-ready"
    }
    print(json.dumps(packet, indent=2))


if __name__ == "__main__":
    main()
