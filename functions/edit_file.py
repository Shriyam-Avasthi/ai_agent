import os

from .workspace_state import editor_instance


def edit_file(
    working_dir: str, file_path: str, search_text: str, replace_text: str
) -> str:
    abs_working_dir = os.path.abspath(working_dir)
    abs_file_path = os.path.abspath(os.path.join(working_dir, file_path))
    if not abs_file_path.startswith(abs_working_dir):
        return f'Error: "{file_path}" is not in the working directory.'
    if not os.path.exists(abs_file_path):
        return f"Error: File {file_path} not found."
    if not os.path.isfile(abs_file_path):
        return f"Error: {file_path} is not a file."

    try:
        return editor_instance.apply_search_replace(
            abs_file_path, search_text, replace_text
        )
    except Exception as e:
        return f"System Error applying patch: {e}"


schema_edit_file = {
    "type": "function",
    "function": {
        "name": "edit_file",
        "description": "Applies a code patch using exact string matching (Aider pattern). You MUST provide the exact existing code in the search_text field. Do not skip lines or change the formatting of the existing code. The replacement text will auto-align to the file's original indentation.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The relative path to the file you want to edit.",
                },
                "search_text": {
                    "type": "string",
                    "description": "The EXACT existing code block you want to replace. Must match the file text perfectly.",
                },
                "replace_text": {
                    "type": "string",
                    "description": "The new code that will replace the search_text block.",
                },
            },
            "required": ["file_path", "search_text", "replace_text"],
        },
    },
}
