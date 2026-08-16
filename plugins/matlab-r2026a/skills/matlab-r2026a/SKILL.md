---
name: matlab-r2026a
description: Use an installed MATLAB R2026a runtime to inspect MATLAB, query help, list installed products, run MATLAB code, or execute .m and .mlx scripts. Use for local MATLAB computation, debugging, script execution, toolbox checks, and version-sensitive R2026a work. Do not use for Octave, a different MATLAB release, or merely editing MATLAB source when execution is not needed.
---

# MATLAB R2026a

Use the MATLAB R2026a MCP tools supplied by this plugin when the user wants local MATLAB execution or installation information.

This is an unofficial community plugin and is not affiliated with or endorsed by MathWorks.

## Choose the smallest tool that fits

- Use `matlab_info` to confirm the release, update, architecture, and MATLAB root.
- Use `list_matlab_products` to see installed MathWorks products and versions.
- Use `get_matlab_help` for authoritative help text from this installation.
- Use `run_matlab_code` for short expressions, calculations, or focused diagnostics.
- Use `run_matlab_script` for an existing `.m` or `.mlx` file.

## Execution workflow

1. Pass an absolute `working_directory` when running project code so relative paths and generated files land in the user's project.
2. Prefer `run_matlab_script` when a script already exists. Use `run_matlab_code` for brief commands or when the user explicitly supplies code to run.
3. Set a longer timeout only when the workload needs it. MATLAB startup itself can take tens of seconds.
4. Report MATLAB errors and warnings faithfully. Distinguish startup or license failures from errors in the user's code.
5. Each tool call starts a fresh noninteractive MATLAB process, so variables and in-memory state do not persist between calls. Put dependent steps in one call or a script.
6. If discovery or release validation fails, ask the user to install R2026a in a standard location or set `MATLAB_R2026A_EXE` to the absolute executable path and restart Codex. Do not bypass the release check with another MATLAB version.

## Safety

MATLAB code can read, create, modify, or delete local files, access networks, and launch external programs. Treat `run_matlab_code` and `run_matlab_script` as general local code execution. Do not run destructive or unrelated code unless the user clearly requests it, and keep working directories inside the user's intended project whenever possible.

Do not imply that every installed product is licensed for the current invocation. `list_matlab_products` reports installation metadata; license availability can still differ.
