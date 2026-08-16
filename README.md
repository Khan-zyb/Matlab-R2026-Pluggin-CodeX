# MATLAB R2026a Codex Plugin (Unofficial)

Run a local MATLAB R2026a installation from Codex through five MCP tools for installation inspection, product listing, MATLAB help, code execution, and script execution.

This is an independent community project. It is not affiliated with or endorsed by The MathWorks, Inc. MATLAB is a registered trademark of The MathWorks, Inc.

## Requirements

- Windows 10 or 11
- MATLAB R2026a with a license that permits noninteractive `-batch` use
- Python 3.10 or newer available as `python` to the Codex desktop app
- Codex or ChatGPT desktop with local plugin marketplace support

The server contains best-effort discovery paths for macOS and Linux, but this release is tested and supported on Windows only.

## Install from a cloned repository

```powershell
git clone https://github.com/Khan-zyb/Matlab-R2026-Pluggin-CodeX.git
cd Matlab-R2026-Pluggin-CodeX
codex plugin marketplace add .
codex plugin add matlab-r2026a@matlab-tools
```

After installation, start a new Codex task so the MCP tools and skill are loaded.

After this publication branch is merged, users can add the GitHub marketplace without cloning first:

```powershell
codex plugin marketplace add Khan-zyb/Matlab-R2026-Pluggin-CodeX
codex plugin add matlab-r2026a@matlab-tools
```

## MATLAB discovery

The server checks these locations in order:

1. The `MATLAB_R2026A_EXE` environment variable.
2. Standard R2026a installation directories for the current operating system.
3. A `matlab` executable available on `PATH`.

Every execution validates `version('-release')` before running user code and refuses releases other than R2026a. If using a nonstandard installation, set `MATLAB_R2026A_EXE` to the absolute path to `matlab.exe`, restart Codex, and try again.

## Tools

- `matlab_info` — return release, update, architecture, and installation root
- `list_matlab_products` — return installed MathWorks product metadata
- `get_matlab_help` — query help from the installed R2026a release
- `run_matlab_code` — execute MATLAB statements in a fresh process
- `run_matlab_script` — execute an existing `.m` or `.mlx` file

Each call starts a fresh MATLAB process. In-memory variables do not persist between calls.

## Security

The execution tools run arbitrary local MATLAB code with the current user's permissions. They can read, create, modify, or delete files, access networks, and launch external programs. Review code before running it and pass an explicit project working directory.

See [SECURITY.md](SECURITY.md) for the security model and reporting guidance.

## Development

```powershell
python -m unittest discover -s tests -v
python -m py_compile plugins/matlab-r2026a/scripts/matlab_mcp_server.py
```

An integration smoke test requires MATLAB R2026a and is performed by sending an MCP `matlab_info` tool call to the server. The repository's automated tests do not require MATLAB.

## License

The plugin source is released under the MIT License. MATLAB itself is proprietary software and is not included.
