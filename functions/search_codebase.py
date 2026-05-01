from functions.workspace_state import searcher_instance


def search_codebase(working_dir: str, regex_pattern: str) -> str:
    try:
        return searcher_instance.search_codebase(working_dir, regex_pattern)
    except Exception as e:
        return f"System Error during search: {e}"


schema_search_codebase = {
    "type": "function",
    "function": {
        "name": "search_codebase",
        "description": "Searches the codebase using ripgrep and returns results mapped to their structural Block IDs (blk_). Use this to find where variables, APIs, or text are used. DO NOT use this to read a whole file. Once you find the match, use 'expand_block' on the returned Block ID to view or edit the exact code.",
        "parameters": {
            "type": "object",
            "properties": {
                "regex_pattern": {
                    "type": "string",
                    "description": "The regular expression or string pattern to search for..",
                },
            },
            "required": ["regex_pattern"],
        },
    },
}
