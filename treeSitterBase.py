from tree_sitter import Language, Parser
import tree_sitter_python as tspython

class TreeSitterBase:
    def __init__(self):
        # Initialize parser once for all subclasses
        PY_LANGUAGE = Language(tspython.language())
        self.parser = Parser(PY_LANGUAGE)

    def _read_file(self, file_path):
        """Standardized file reading."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def _get_text(self, node, source_bytes):
        """Extracts exact text for a node from source bytes."""
        return source_bytes[node.start_byte:node.end_byte].decode("utf8")

    def _get_name(self, node, source_bytes):
        """Safe extraction of a function/class name."""
        name_node = node.child_by_field_name('name')
        if name_node:
            return self._get_text(name_node, source_bytes)
        return "anon"

