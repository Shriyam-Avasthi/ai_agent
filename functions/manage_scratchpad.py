# functions/manage_scratchpad.py
import os


def manage_scratchpad(working_directory: str, action: str, content: str = "") -> str:
    scratchpad_path = os.path.join(working_directory, ".agent_scratchpad.txt")

    if action == "clear":
        with open(scratchpad_path, "w") as f:
            f.write("")
        return "Scratchpad cleared."

    elif action == "update":
        with open(scratchpad_path, "w") as f:
            f.write(content)
        return "Scratchpad updated successfully."

    elif action == "append":
        with open(scratchpad_path, "a") as f:
            f.write("\n" + content)
        return "Content appended to scratchpad."

    return "Error: Invalid action."


schema_manage_scratchpad = {
    "type": "function",
    "function": {
        "name": "manage_scratchpad",
        "description": "This is your scratchpad. Use it to write down long-term goals, active stack traces, or to-do lists. This information will NEVER be forgotten or summarized. Update it when you start a complex task, and clear it when the task is done. The contents of this scratchpad are automatically added to the active message history.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["update", "append", "clear"]},
                "content": {
                    "type": "string",
                    "description": "The exact text, stack trace, or plan to save.",
                },
            },
            "required": ["action"],
        },
    },
}
