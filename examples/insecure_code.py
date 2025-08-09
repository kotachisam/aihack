# examples/insecure_code.py
# type: ignore  # This file contains intentional security issues for AI analysis

import subprocess
from typing import Any, Dict

import flask  # type: ignore[import-untyped]

app = flask.Flask(__name__)


@app.route("/run")
def run_command() -> Dict[str, str]:
    """A highly insecure function that runs a command from a query parameter."""
    command = flask.request.args.get("command")

    # CWE-78: Improper Neutralization of Special Elements used in an OS Command ('OS Command Injection')
    # This is a major security vulnerability!
    subprocess.run(command, shell=True)

    return {"status": "command executed"}


def get_file_contents(request: Any) -> str:
    """Another insecure function that reads a file path from a request."""
    filename = request.json.get("filename")

    # CWE-22: Improper Limitation of a Pathname to a Restricted Directory ('Path Traversal')
    # An attacker could read any file on the system.
    with open(filename, "r") as f:
        return f.read()


# To test with aihack:
# ah review examples/insecure_code.py --model gemini --focus security
