# Security policy

## Security model

`run_matlab_code` and `run_matlab_script` intentionally execute local MATLAB code with the current user's permissions. They are marked as write-capable, potentially destructive, and open-world in their MCP tool annotations because MATLAB code can also access networks and external programs.

The plugin does not provide authentication, isolation, or a separate sandbox. Users should review code before execution, use an explicit project working directory, and avoid running untrusted scripts.

The server launches MATLAB without a shell, caps captured output, enforces a configurable timeout, and terminates the MATLAB process tree after a timeout. It also refuses MATLAB releases other than R2026a.

## Reporting a vulnerability

Use the repository's private security-advisory feature when available. Do not include license keys, proprietary MATLAB files, personal paths, or other secrets in public reports.
