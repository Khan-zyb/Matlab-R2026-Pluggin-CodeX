# MATLAB R2026a (Unofficial)

This plugin runs a locally installed MATLAB R2026a runtime through a dependency-free Python MCP server.

## Runtime requirements

- Windows 10 or 11
- MATLAB R2026a and an appropriate license
- Python 3.10+ available as `python`

The server first honors `MATLAB_R2026A_EXE`, then checks the standard R2026a installation directory, then checks `PATH`. It validates that the selected executable reports R2026a before running any requested code.

## Available tools

- `matlab_info`
- `list_matlab_products`
- `get_matlab_help`
- `run_matlab_code`
- `run_matlab_script`

Each call starts a fresh MATLAB process. The execution tools run with the current user's local permissions and may modify files.

This is an independent community project and is not affiliated with or endorsed by The MathWorks, Inc.
