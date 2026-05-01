# functions/get_file_skeleton.py
import os

from functions.workspace_state import skeletonizer_instance


def get_file_skeleton(working_directory: str, file_path: str) -> str:
    abs_working_dir = os.path.abspath(working_directory)
    abs_file_path = os.path.abspath(os.path.join(working_directory, file_path))
    if not abs_file_path.startswith(abs_working_dir):
        return f'Error: "{file_path}" is not in the working directory.'
    if not os.path.exists(abs_file_path):
        return f"Error: File {file_path} not found."
    if not os.path.isfile(abs_file_path):
        return f"Error: {file_path} is not a file."

    try:
        return skeletonizer_instance.generate_skeleton(abs_file_path)
    except Exception as e:
        return f"System Error parsing skeleton: {e}"


schema_get_file_skeleton = {
    "type": "function",
    "function": {
        "name": "get_file_skeleton",
        "description": "Reads the high-level structural outline of a Python file. Always use this BEFORE trying to edit a file. It returns function signatures and unique Block IDs (e.g., blk_1a2b3c) that you can use to zoom in on specific logic.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The relative path to the Python file you want to map (e.g., 'src/main.py').",
                }
            },
            "required": ["file_path"],
        },
    },
}
