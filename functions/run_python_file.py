import os
import subprocess
import sys


def run_python_file(working_dir: str, file_path: str, cli_args: list | None = None) -> str:
    full_path = os.path.join(working_dir, file_path)
    abs_working_dir = os.path.abspath(working_dir)
    abs_file_path = os.path.abspath(os.path.join(working_dir, file_path))

    if not os.path.exists(full_path):
        return f"Error: File {file_path} not found in workspace."
    if not abs_file_path.startswith(abs_working_dir):
        return f'Error: "{file_path}" is not in the working directory.'
    if not os.path.isfile(abs_file_path):
        return f"Error: {file_path} is not a file."
    if not file_path.endswith(".py"):
        return f'Error: "{file_path}" is not a python file.'

    outputs_dir = os.path.join(abs_working_dir, "outputs")
    os.makedirs(outputs_dir, exist_ok=True)

    # sys.executable points to the python binary currently running this script (e.g., .venv/bin/python)
    venv_python = sys.executable

    cmd = [
        "bwrap",
        "--unshare-net",
        "--die-with-parent",
        # MOUNT 1: The entire host OS as Strictly READ-ONLY
        "--ro-bind",
        "/", "/",
        # MOUNT 2: Dev and Proc (Required for Python to function)
        "--dev", "/dev",
        "--proc", "/proc",
        # MOUNT 3: A fresh, isolated /tmp folder in memory
        "--tmpfs", "/tmp",
        # MOUNT 4: The outputs folder as READ-WRITE
        "--bind",
        outputs_dir,
        outputs_dir,
        "--chdir", abs_working_dir,  # Set working directory
        venv_python, file_path,  # Run the script using the active venv
    ]

    if cli_args:
        cmd.extend(cli_args)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)

        output = []
        if result.stdout:
            output.append(f"--- STDOUT ---\n{result.stdout.strip()}")
        if result.stderr:
            output.append(f"--- STDERR ---\n{result.stderr.strip()}")

        if not output:
            return "Execution completed successfully with no output."

        return "\n".join(output)

    except subprocess.TimeoutExpired:
        return "Error: Execution timed out after 15 seconds. You might have an infinite loop."
    except Exception as e:
        return f"System Error during sandbox execution: {str(e)}"


schema_run_python_file = {
    "type": "function",
    "function": {
        "name": "run_python_file",
        "description": "Runs a python file with the python3 interpreter. Accepts additional CLI args as an optional array.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The file to run, relative to the current working directory.",
                },
                "args": {
                    "type": "array",
                    "description": "An optional array of strings to be used as the CLI args for the Python file.",
                    "items": {"type": "string"},
                },
            },
            "required": ["file_path"],
        },
    },
}
