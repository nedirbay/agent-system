"""Scratch-confined desktop driver (Faza 7 Task 22).

Unlike the simulated browser, this driver performs *real* file operations and
process execution — but only inside the sandbox scratch volume (SB-002) and
only with allowlisted commands (SB-003), bounded by a wall-clock timeout
(SB-006). Paths and commands are re-validated here (defence in depth) even
though the sandbox already classified the action.
"""
from __future__ import annotations

import asyncio
from pathlib import Path

from app.modules.execution.application.sandbox import SafeExecutionSandbox
from app.modules.execution.domain import actions as A
from app.modules.execution.domain.drivers import DesktopDriver, DriverResult
from app.modules.execution.domain.sandbox import SafeExecutionError, SandboxPolicy


class LocalSandboxDesktopDriver(DesktopDriver):
    def __init__(self, policy: SandboxPolicy) -> None:
        self._policy = policy
        self._sandbox = SafeExecutionSandbox(policy)
        policy.scratch_dir.mkdir(parents=True, exist_ok=True)

    async def execute(self, action: A.Action) -> DriverResult:
        handlers = {
            A.READ_FILE: self._read_file,
            A.WRITE_FILE: self._write_file,
            A.LIST_DIR: self._list_dir,
            A.RUN_PROCESS: self._run_process,
        }
        handler = handlers.get(action.type)
        if handler is None:  # delete_file is forbidden upstream; never reaches here
            raise SafeExecutionError(f"Unsupported desktop action '{action.type}'")
        return await handler(action.params)

    def _resolve(self, path: str | None) -> Path:
        if not path:
            raise SafeExecutionError("Missing path")
        resolved = self._sandbox.resolve_in_scratch(path)
        if resolved is None:
            raise SafeExecutionError(f"Path '{path}' escapes the scratch volume")
        return resolved

    async def _read_file(self, params: dict) -> DriverResult:
        target = self._resolve(params.get("path"))
        if not target.is_file():
            raise SafeExecutionError(f"File not found: {params.get('path')}")
        content = target.read_text(encoding="utf-8", errors="replace")
        content = content[: self._policy.max_output_chars]
        return DriverResult(
            output={"path": params.get("path"), "content": content, "bytes": len(content)},
            logs=[f"read {params.get('path')}"],
        )

    async def _write_file(self, params: dict) -> DriverResult:
        target = self._resolve(params.get("path"))
        content = params.get("content", "")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return DriverResult(
            output={"path": params.get("path"), "bytes": len(content)},
            logs=[f"wrote {params.get('path')}"],
        )

    async def _list_dir(self, params: dict) -> DriverResult:
        target = self._resolve(params.get("path") or ".")
        if not target.is_dir():
            raise SafeExecutionError(f"Directory not found: {params.get('path')}")
        entries = sorted(p.name for p in target.iterdir())
        return DriverResult(
            output={"path": params.get("path") or ".", "entries": entries},
            logs=[f"listed {params.get('path') or '.'}"],
        )

    async def _run_process(self, params: dict) -> DriverResult:
        command = params.get("command")
        args = [str(a) for a in params.get("args", [])]
        if not command or Path(command).name not in self._policy.command_allowlist:
            raise SafeExecutionError(f"Command '{command}' is not allowlisted")

        proc = await asyncio.create_subprocess_exec(
            command,
            *args,
            cwd=str(self._policy.scratch_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=self._policy.process_timeout_seconds
            )
        except asyncio.TimeoutError as exc:
            proc.kill()
            await proc.wait()
            raise SafeExecutionError(
                f"Process exceeded {self._policy.process_timeout_seconds}s limit (SB-006)"
            ) from exc

        limit = self._policy.max_output_chars
        return DriverResult(
            output={
                "command": command,
                "args": args,
                "returncode": proc.returncode,
                "stdout": stdout.decode("utf-8", "replace")[:limit],
                "stderr": stderr.decode("utf-8", "replace")[:limit],
            },
            logs=[f"ran {command} (exit {proc.returncode})"],
        )
