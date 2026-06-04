from __future__ import annotations

import asyncio
import logging
import os
import shutil
from pathlib import Path
from dataclasses import dataclass
from typing import Mapping

from bot.core.config import sanitize_text
from bot.core.errors import MissingUtilityError, ProcessExecutionError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CommandResult:
    args: list[str]
    returncode: int
    stdout: str
    stderr: str


class CommandRunner:
    async def run(
        self,
        args: list[str],
        *,
        cwd: str | None = None,
        env: Mapping[str, str] | None = None,
        input_text: str | None = None,
        timeout: float | None = None,
        check: bool = True,
    ) -> CommandResult:
        if not args:
            raise ValueError("Empty command args")
        if shutil.which(args[0]) is None and "/" not in args[0]:
            raise MissingUtilityError(f"Утилита не найдена: {args[0]}")

        safe_args = [sanitize_text(part) for part in args]
        logger.info("Run command: %s", safe_args)
        process = await asyncio.create_subprocess_exec(
            *args,
            cwd=cwd,
            env={**os.environ, **dict(env)} if env else None,
            stdin=asyncio.subprocess.PIPE if input_text is not None else None,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_b, stderr_b = await asyncio.wait_for(
            process.communicate(input_text.encode() if input_text is not None else None),
            timeout=timeout,
        )
        stdout = stdout_b.decode(errors="replace")
        stderr = stderr_b.decode(errors="replace")
        result = CommandResult(args=args, returncode=process.returncode or 0, stdout=stdout, stderr=stderr)
        if stderr:
            logger.warning("Command stderr (%s): %s", safe_args, sanitize_text(stderr[:4000]))
        if check and result.returncode != 0:
            raise ProcessExecutionError(
                f"Команда завершилась с кодом {result.returncode}: {safe_args[0]}",
                returncode=result.returncode,
                stderr=stderr,
            )
        return result

    async def run_with_stdin_file(
        self,
        args: list[str],
        *,
        input_path: Path,
        cwd: str | None = None,
        env: Mapping[str, str] | None = None,
        timeout: float | None = None,
        check: bool = True,
    ) -> CommandResult:
        if not args:
            raise ValueError("Empty command args")
        if shutil.which(args[0]) is None and "/" not in args[0]:
            raise MissingUtilityError(f"Утилита не найдена: {args[0]}")

        safe_args = [sanitize_text(part) for part in args]
        logger.info("Run command: %s < %s", safe_args, sanitize_text(str(input_path)))
        with input_path.open("rb") as stdin_file:
            process = await asyncio.create_subprocess_exec(
                *args,
                cwd=cwd,
                env={**os.environ, **dict(env)} if env else None,
                stdin=stdin_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout_b, stderr_b = await asyncio.wait_for(process.communicate(), timeout=timeout)
        stdout = stdout_b.decode(errors="replace")
        stderr = stderr_b.decode(errors="replace")
        result = CommandResult(args=args, returncode=process.returncode or 0, stdout=stdout, stderr=stderr)
        if stderr:
            logger.warning("Command stderr (%s): %s", safe_args, sanitize_text(stderr[:4000]))
        if check and result.returncode != 0:
            raise ProcessExecutionError(
                f"Команда завершилась с кодом {result.returncode}: {safe_args[0]}",
                returncode=result.returncode,
                stderr=stderr,
            )
        return result
