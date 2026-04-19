# OpenHarness setup (this repo)

OpenHarness is the agent harness referenced in [`AGENTS.md`](AGENTS.md). Upstream docs: [OpenHarness README](https://github.com/HKUDS/OpenHarness/blob/main/README.md), [SHOWCASE](https://github.com/HKUDS/OpenHarness/blob/main/docs/SHOWCASE.md).

## Prerequisites

- Python **3.11+** (tested with 3.11.2)

## Install (local venv)

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If you prefer not to activate the venv, call the CLI by path:

```powershell
.\.venv\Scripts\oh.exe --version
```

## Windows PowerShell note

The bare command `oh` can conflict with PowerShell’s built-in **`Out-Host`** alias. Prefer:

- `.\.venv\Scripts\oh.exe` after `cd` to the repo, or  
- Activate the venv and still use `oh.exe` if `oh` misbehaves.

## Configure provider (once per machine)

Interactive wizard (API keys / subscription flows live here):

```powershell
.\.venv\Scripts\oh.exe setup
```

Equivalent upstream: `oh setup` on macOS/Linux.

## Run the harness

```powershell
.\.venv\Scripts\oh.exe
```

Non-interactive one-shot:

```powershell
.\.venv\Scripts\oh.exe -p "Summarize AGENTS.md" --output-format json
```

## MCP (for mocked company tools)

```powershell
.\.venv\Scripts\oh.exe mcp --help
```

Use `--mcp-config` on `oh` when you need to load MCP server definitions from JSON (see upstream CLI help).

## Optional: official one-liner install

Instead of `pip install -r requirements.txt`, upstream also documents a PowerShell installer; the venv + `requirements.txt` approach keeps versions aligned for the team.
