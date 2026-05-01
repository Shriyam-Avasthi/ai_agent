from .workspace_state import skeletonizer_instance


def expand_block(block_id: str, max_lines: int = 50) -> str:
    if max_lines > 100:
        return f"Error: Too Many lines requested. max_lines should be less than 100."
    if not block_id.startswith("blk_"):
        return "Error: Invalid block ID format. Must start with 'blk_'."

    try:
        return skeletonizer_instance.expand_block(block_id, max_lines)
    except Exception as e:
        return f"Error expanding block: {e}"


schema_expand_block = {
    "type": "function",
    "function": {
        "name": "expand_block",
        "description": "Reveals the hidden inner code of a specific Block ID. You MUST call get_file_skeleton first to obtain valid Block IDs. If the block is very large, this tool will return a deeper structural map with new, inner Block IDs.",
        "parameters": {
            "type": "object",
            "properties": {
                "block_id": {
                    "type": "string",
                    "description": "The exact block ID to expand, starting with 'blk_' (e.g., 'blk_a1b2c3d4').",
                },
                "max_lines": {
                    "type": "integer",
                    "description": "The maximum number of lines to return before re-folding inner blocks. Default is 50.",
                },
            },
            "required": ["block_id"],
        },
    },
}
