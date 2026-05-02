from functions.browser_controller import browser_controller_instance

def browser_navigate(url: str) -> str:
    return browser_controller_instance.navigate(url)

def browser_action(action_type: str, element_id: str, text: str = "") -> str:
    return browser_controller_instance.action(action_type, element_id, text)

def browser_extract(selector: str) -> str:
    return browser_controller_instance.extract_text(selector)

schema_browser_navigate = {
    "type": "function",
    "function": {
        "name": "browser_navigate",
        "description": "Navigates the persistent browser to a URL. Returns a DOM Map.",
        "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}
    }
}

schema_browser_action = {
    "type": "function",
    "function": {
        "name": "browser_action",
        "description": "Interacts with the live browser.",
        "parameters": {
            "type": "object",
            "properties": {
                "action_type": {
                    "type": "string", 
                    "enum": ["click", "type", "hover", "scroll_down", "scroll_up"]
                },
                "element_id": {"type": "string", "description": "Leave empty if scrolling."},
                "text": {"type": "string"}
            },
            "required": ["action_type"]
        }
    }
}

schema_browser_extract = {
    "type": "function",
    "function": {
        "name": "browser_extract",
        "description": "Extracts raw, readable text from the current webpage. Use this to read articles, documentation, or problem statements.",
        "parameters": {
            "type": "object",
            "properties": {
                "selector": {
                    "type": "string",
                    "description": "The CSS selector to extract text from (e.g., 'body', 'main', '.problem-statement'). Default is 'body'."
                }
            }
        }
    }
}
