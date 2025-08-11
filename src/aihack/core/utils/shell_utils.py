"""Pure utility functions for safe shell command execution."""
import asyncio
import os
from typing import Any, Dict


async def execute_shell_command(command: str, timeout: float = 10.0) -> Dict[str, Any]:
    """Execute a shell command safely with timeout and output limits.

    Args:
        command: Shell command to execute
        timeout: Timeout in seconds (default 10.0)

    Returns:
        Dictionary with execution results including stdout, stderr, return_code, and success
    """
    try:
        # Use asyncio subprocess for proper async handling
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=os.getcwd(),
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )
            stdout_text = stdout.decode("utf-8", errors="replace") if stdout else ""
            stderr_text = stderr.decode("utf-8", errors="replace") if stderr else ""
            return_code = process.returncode
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Command timed out after {timeout} seconds",
                "return_code": -1,
                "timed_out": True,
            }

        # Limit output size to prevent terminal flooding
        max_output = 2000
        if len(stdout_text) > max_output:
            stdout_text = stdout_text[:max_output] + "\n... (output truncated)"
        if len(stderr_text) > max_output:
            stderr_text = stderr_text[:max_output] + "\n... (output truncated)"

        return {
            "success": return_code == 0,
            "stdout": stdout_text,
            "stderr": stderr_text,
            "return_code": return_code,
            "timed_out": False,
        }

    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Shell execution error: {str(e)}",
            "return_code": -1,
            "timed_out": False,
        }


def format_shell_output(result: Dict[str, Any], command: str) -> str:
    """Format shell command execution results for display.

    Args:
        result: Result dictionary from execute_shell_command
        command: Original command that was executed

    Returns:
        Formatted output string for display
    """
    if result["timed_out"]:
        return "❌ Command timed out after 10 seconds (use /help for safe commands)\n"

    stdout_text = result["stdout"]
    stderr_text = result["stderr"]
    return_code = result["return_code"]

    if return_code == 0:
        if stdout_text or stderr_text:
            return f"🔧 **Shell Output:**\n```\n{stdout_text}{stderr_text}\n```\n"
        else:
            return "✅ Command completed successfully (no output)\n"
    else:
        return f"❌ **Shell Error (exit {return_code}):**\n```\n{stderr_text}\n{stdout_text}\n```\n"


async def check_command_availability(command: str) -> bool:
    """Check if a command is available on the system.

    Args:
        command: Command name to check

    Returns:
        True if command is available, False otherwise
    """
    try:
        result = await execute_shell_command(f"which {command}", timeout=5.0)
        return bool(result["success"])
    except Exception:
        return False
