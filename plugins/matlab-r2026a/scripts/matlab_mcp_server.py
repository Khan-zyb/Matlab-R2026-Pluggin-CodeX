#!/usr/bin/env python3
"""Dependency-free MCP server for a local MATLAB R2026a installation."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any


SERVER_NAME = "MATLAB R2026a MCP"
SERVER_VERSION = "0.2.0"
EXPECTED_RELEASE = "2026a"
MAX_OUTPUT_CHARS = 120_000
MAX_CODE_CHARS = 200_000
DEFAULT_TIMEOUT_SECONDS = 300
MAX_TIMEOUT_SECONDS = 3600

METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603


TOOLS: list[dict[str, Any]] = [
    {
        "name": "matlab_info",
        "title": "Inspect MATLAB R2026a",
        "description": (
            "Start the configured MATLAB executable and return its release, full version, "
            "architecture, and installation root."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "timeout_seconds": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": MAX_TIMEOUT_SECONDS,
                    "default": 120,
                    "description": "Maximum runtime, including MATLAB startup.",
                }
            },
            "additionalProperties": False,
        },
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    {
        "name": "list_matlab_products",
        "title": "List Installed MATLAB Products",
        "description": (
            "Return MATLAB and installed MathWorks product names, versions, releases, and dates. "
            "Installation does not guarantee that a product is licensed for every use."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "timeout_seconds": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": MAX_TIMEOUT_SECONDS,
                    "default": 180,
                    "description": "Maximum runtime, including MATLAB startup.",
                }
            },
            "additionalProperties": False,
        },
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    {
        "name": "get_matlab_help",
        "title": "Get MATLAB Help",
        "description": (
            "Return installed MATLAB help text for a function, class, package, or topic such as "
            "plot, table.join, or matlabRelease."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "minLength": 1,
                    "description": "MATLAB help topic.",
                },
                "timeout_seconds": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": MAX_TIMEOUT_SECONDS,
                    "default": 180,
                    "description": "Maximum runtime, including MATLAB startup.",
                },
            },
            "required": ["topic"],
            "additionalProperties": False,
        },
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    {
        "name": "run_matlab_code",
        "title": "Run MATLAB Code",
        "description": (
            "Run MATLAB statements in a fresh noninteractive R2026a process. The code can access "
            "local files, external programs, and networks with the current user's permissions."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "minLength": 1,
                    "description": "MATLAB statements to execute with the -batch startup option.",
                },
                "working_directory": {
                    "type": "string",
                    "description": (
                        "Absolute directory used as MATLAB's process working directory. "
                        "Use the user's project directory for project code."
                    ),
                },
                "timeout_seconds": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": MAX_TIMEOUT_SECONDS,
                    "default": DEFAULT_TIMEOUT_SECONDS,
                    "description": "Maximum runtime, including MATLAB startup.",
                },
            },
            "required": ["code"],
            "additionalProperties": False,
        },
        "annotations": {
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": False,
            "openWorldHint": True,
        },
    },
    {
        "name": "run_matlab_script",
        "title": "Run MATLAB Script",
        "description": (
            "Run an existing .m or .mlx script in a fresh noninteractive R2026a process. The "
            "script can access local files, external programs, and networks with the current "
            "user's permissions."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "script_path": {
                    "type": "string",
                    "minLength": 1,
                    "description": "Absolute script path, or a path relative to working_directory.",
                },
                "working_directory": {
                    "type": "string",
                    "description": (
                        "Absolute process working directory. If omitted, the script's parent "
                        "directory is used."
                    ),
                },
                "timeout_seconds": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": MAX_TIMEOUT_SECONDS,
                    "default": DEFAULT_TIMEOUT_SECONDS,
                    "description": "Maximum runtime, including MATLAB startup.",
                },
            },
            "required": ["script_path"],
            "additionalProperties": False,
        },
        "annotations": {
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": False,
            "openWorldHint": True,
        },
    },
]


def send(message: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(message, ensure_ascii=False, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def send_result(request_id: Any, result: dict[str, Any]) -> None:
    send({"jsonrpc": "2.0", "id": request_id, "result": result})


def send_error(request_id: Any, code: int, message: str) -> None:
    send({"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}})


def require_object(value: Any, name: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object.")
    return value


def require_string(value: Any, name: str, *, max_chars: int = MAX_CODE_CHARS) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string.")
    if len(value) > max_chars:
        raise ValueError(f"{name} must be no longer than {max_chars} characters.")
    return value


def parse_timeout(value: Any, default: int) -> int:
    if value is None:
        return default
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("timeout_seconds must be an integer.")
    if not 1 <= value <= MAX_TIMEOUT_SECONDS:
        raise ValueError(f"timeout_seconds must be between 1 and {MAX_TIMEOUT_SECONDS}.")
    return value


def resolve_working_directory(value: Any) -> Path:
    if value is None:
        path = Path.cwd()
    else:
        raw = require_string(value, "working_directory", max_chars=32_000)
        path = Path(raw).expanduser()
        if not path.is_absolute():
            raise ValueError("working_directory must be an absolute path.")
    path = path.resolve()
    if not path.is_dir():
        raise ValueError(f"working_directory does not exist or is not a directory: {path}")
    return path


def matlab_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def matlab_executable_candidates() -> list[Path]:
    """Return MATLAB candidates in preference order without touching the filesystem."""
    raw_candidates: list[str] = []
    override = os.environ.get("MATLAB_R2026A_EXE")
    if override:
        raw_candidates.append(override)

    if os.name == "nt":
        for variable in ("ProgramW6432", "ProgramFiles", "ProgramFiles(x86)"):
            program_files = os.environ.get(variable)
            if program_files:
                raw_candidates.append(
                    str(Path(program_files) / "MATLAB" / "R2026a" / "bin" / "matlab.exe")
                )
        raw_candidates.append(r"C:\Program Files\MATLAB\R2026a\bin\matlab.exe")
    elif sys.platform == "darwin":
        raw_candidates.append("/Applications/MATLAB_R2026a.app/bin/matlab")
    else:
        raw_candidates.extend(
            [
                "/usr/local/MATLAB/R2026a/bin/matlab",
                "/opt/MATLAB/R2026a/bin/matlab",
            ]
        )

    path_match = shutil.which("matlab")
    if path_match:
        raw_candidates.append(path_match)

    candidates: list[Path] = []
    seen: set[str] = set()
    for raw_candidate in raw_candidates:
        candidate = Path(raw_candidate).expanduser()
        key = os.path.normcase(str(candidate))
        if key not in seen:
            seen.add(key)
            candidates.append(candidate)
    return candidates


def find_matlab_executable() -> Path:
    candidates = matlab_executable_candidates()
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    checked = "\n- ".join(str(candidate) for candidate in candidates)
    raise RuntimeError(
        "MATLAB R2026a executable was not found. Install R2026a in its standard location or "
        "set MATLAB_R2026A_EXE to matlab.exe, then restart Codex. Checked:\n- " + checked
    )


def release_guarded_statement(statement: str) -> str:
    """Fail before user code when the selected executable is not R2026a."""
    expected = matlab_quote(EXPECTED_RELEASE)
    return (
        "codexPluginRelease=version('-release'); "
        f"if ~strcmp(codexPluginRelease,{expected}), "
        "error('matlab-r2026a:WrongRelease',"
        "'Expected MATLAB R2026a but found R%s.',codexPluginRelease); end; "
        "clear codexPluginRelease; "
        + statement
    )


def truncate_output(value: str) -> tuple[str, bool]:
    if len(value) <= MAX_OUTPUT_CHARS:
        return value, False
    half = MAX_OUTPUT_CHARS // 2
    omitted = len(value) - (half * 2)
    marker = f"\n... {omitted} characters omitted by matlab-r2026a ...\n"
    return value[:half] + marker + value[-half:], True


def terminate_process_tree(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    else:
        process.kill()


def run_matlab(statement: str, working_directory: Path, timeout_seconds: int) -> dict[str, Any]:
    matlab_exe = find_matlab_executable()
    guarded_statement = release_guarded_statement(statement)

    creation_flags = 0
    if os.name == "nt":
        creation_flags = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP

    process = subprocess.Popen(
        [str(matlab_exe), "-batch", guarded_statement],
        cwd=str(working_directory),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=creation_flags,
    )

    timed_out = False
    try:
        stdout, stderr = process.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        timed_out = True
        terminate_process_tree(process)
        try:
            stdout, stderr = process.communicate(timeout=15)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()

    stdout, stdout_truncated = truncate_output(stdout or "")
    stderr, stderr_truncated = truncate_output(stderr or "")
    return {
        "exitCode": process.returncode,
        "timedOut": timed_out,
        "timeoutSeconds": timeout_seconds,
        "matlabExecutable": str(matlab_exe),
        "workingDirectory": str(working_directory),
        "stdout": stdout,
        "stderr": stderr,
        "outputTruncated": stdout_truncated or stderr_truncated,
    }


def format_tool_result(result: dict[str, Any]) -> dict[str, Any]:
    if result["timedOut"]:
        status = f"MATLAB timed out after {result['timeoutSeconds']} seconds."
    else:
        status = f"MATLAB exited with code {result['exitCode']}."
    sections = [
        status,
        f"MATLAB executable: {result['matlabExecutable']}",
        f"Working directory: {result['workingDirectory']}",
    ]
    if result["stdout"]:
        sections.append("STDOUT:\n" + result["stdout"].rstrip())
    if result["stderr"]:
        sections.append("STDERR:\n" + result["stderr"].rstrip())
    if result["outputTruncated"]:
        sections.append("Output was truncated by the plugin.")
    is_error = result["timedOut"] or result["exitCode"] != 0
    return {
        "content": [{"type": "text", "text": "\n\n".join(sections)}],
        "structuredContent": result,
        "isError": is_error,
    }


def call_tool(name: str, arguments: Any) -> dict[str, Any]:
    args = require_object(arguments, "arguments")

    if name == "matlab_info":
        timeout = parse_timeout(args.get("timeout_seconds"), 120)
        statement = (
            "info=struct('release',version('-release'),'version',version,"
            "'architecture',computer('arch'),'matlabRoot',matlabroot); "
            "disp(jsonencode(info));"
        )
        return format_tool_result(run_matlab(statement, Path.cwd(), timeout))

    if name == "list_matlab_products":
        timeout = parse_timeout(args.get("timeout_seconds"), 180)
        statement = (
            "v=ver; data=struct('name',{v.Name},'version',{v.Version},"
            "'release',{v.Release},'date',{v.Date}); disp(jsonencode(data));"
        )
        return format_tool_result(run_matlab(statement, Path.cwd(), timeout))

    if name == "get_matlab_help":
        topic = require_string(args.get("topic"), "topic", max_chars=1000).strip()
        timeout = parse_timeout(args.get("timeout_seconds"), 180)
        statement = f"help({matlab_quote(topic)});"
        return format_tool_result(run_matlab(statement, Path.cwd(), timeout))

    if name == "run_matlab_code":
        code = require_string(args.get("code"), "code")
        timeout = parse_timeout(args.get("timeout_seconds"), DEFAULT_TIMEOUT_SECONDS)
        working_directory = resolve_working_directory(args.get("working_directory"))
        return format_tool_result(run_matlab(code, working_directory, timeout))

    if name == "run_matlab_script":
        raw_script = require_string(args.get("script_path"), "script_path", max_chars=32_000)
        requested_working_directory = args.get("working_directory")
        if requested_working_directory is None:
            base = Path.cwd()
        else:
            base = resolve_working_directory(requested_working_directory)
        script_path = Path(raw_script).expanduser()
        if not script_path.is_absolute():
            script_path = base / script_path
        script_path = script_path.resolve()
        if not script_path.is_file():
            raise ValueError(f"script_path does not exist or is not a file: {script_path}")
        if script_path.suffix.lower() not in {".m", ".mlx"}:
            raise ValueError("script_path must refer to a .m or .mlx file.")
        if requested_working_directory is None:
            base = script_path.parent
        timeout = parse_timeout(args.get("timeout_seconds"), DEFAULT_TIMEOUT_SECONDS)
        statement = f"run({matlab_quote(str(script_path))});"
        return format_tool_result(run_matlab(statement, base, timeout))

    raise ValueError(f"Unknown tool: {name}")


def handle_request(message: dict[str, Any]) -> None:
    request_id = message.get("id")
    method = message.get("method")

    if method == "initialize":
        params = message.get("params") if isinstance(message.get("params"), dict) else {}
        send_result(
            request_id,
            {
                "protocolVersion": params.get("protocolVersion", "2025-11-25"),
                "capabilities": {"tools": {}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
                "instructions": (
                    "Use these tools for the local MATLAB R2026a installation. Arbitrary code "
                    "and script execution can modify local files; use the user's intended project "
                    "as working_directory and run only code within the requested scope."
                ),
            },
        )
        return

    if method == "ping":
        send_result(request_id, {})
        return

    if method == "tools/list":
        send_result(request_id, {"tools": TOOLS})
        return

    if method == "tools/call":
        params = require_object(message.get("params"), "params")
        name = require_string(params.get("name"), "name", max_chars=200)
        send_result(request_id, call_tool(name, params.get("arguments")))
        return

    if request_id is not None:
        send_error(request_id, METHOD_NOT_FOUND, f"Method not found: {method}")


def main() -> None:
    for raw_line in sys.stdin:
        if not raw_line.strip():
            continue
        try:
            message = json.loads(raw_line)
            if not isinstance(message, dict):
                raise ValueError("MCP message must be a JSON object.")
            handle_request(message)
        except ValueError as error:
            request_id = message.get("id") if isinstance(locals().get("message"), dict) else None
            send_error(request_id, INVALID_PARAMS, str(error))
        except Exception as error:  # Keep diagnostics on the protocol, never stdout.
            request_id = message.get("id") if isinstance(locals().get("message"), dict) else None
            print(f"{SERVER_NAME}: {error}", file=sys.stderr, flush=True)
            send_error(request_id, INTERNAL_ERROR, str(error))


if __name__ == "__main__":
    main()
