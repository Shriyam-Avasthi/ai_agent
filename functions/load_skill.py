import os

def load_skill(skill_name: str) -> str:
    skill_path = f"skills/{skill_name}.md"
    if os.path.exists(skill_path):
        with open(skill_path, "r") as f:
            return f.read()
    return f"Error: Skill '{skill_name}' not found. Available skills: browser."

schema_load_skill = {
    "type": "function",
    "function": {
        "name": "load_skill",
        "description": "Loads the manual and code templates for advanced skills (like 'browser'). Call this BEFORE attempting advanced tasks.",
        "parameters": {
            "type": "object",
            "properties": {
                "skill_name": {"type": "string"}
            },
            "required": ["skill_name"]
        }
    }
}
