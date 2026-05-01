import os


def list_directory(working_dir: str, target_dir: str = ".") -> str:
    abs_working_dir = os.path.abspath(working_dir)
    abs_directory = os.path.abspath(os.path.join(working_dir, target_dir))
    if not abs_directory.startswith(abs_working_dir):
        return f'Error: "{target_dir}" is not in the working directory.'

    if not os.path.exists(abs_directory):
        return f"Error: Directory {abs_directory} not found."

    ignore_dirs = {
        ".git",
        "__pycache__",
        "node_modules",
        ".venv",
        "venv",
        ".pytest_cache",
    }
    tree_output = []

    for root, dirs, files in os.walk(abs_directory):
        # Mutate dirs in-place to skip ignored directories
        dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith(".")]

        level = root.replace(abs_directory, "").count(os.sep)
        indent = " " * 4 * level
        folder_name = os.path.basename(root) or target_dir

        tree_output.append(f"{indent} [FOLDER] {folder_name}/")

        sub_indent = " " * 4 * (level + 1)
        for f in sorted(files):
            if not f.endswith(".pyc"):
                tree_output.append(f"{sub_indent} [FILE] {f}")

    return "\n".join(tree_output)


schema_list_directory = {
    "type": "function",
    "function": {
        "name": "list_directory",
        "description": "Explores the repository structure. Use this first to understand the layout of the project before reading files. Returns a clean, token-efficient tree view of folders and files.",
        "parameters": {
            "type": "object",
            "properties": {
                "target_dir": {
                    "type": "string",
                    "description": "The specific directory to list. Default is '.' for the root.",
                }
            },
            "required": ["target_dir"],
        },
    },
}
