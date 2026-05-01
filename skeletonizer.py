import hashlib

from treeSitterBase import TreeSitterBase


class CodeSkeletonizer(TreeSitterBase):
    def __init__(self):
        super().__init__()
        self.block_registry = {}

    def _generate_block_id(self, file_path, node):
        unique_str = f"{file_path}_{node.start_byte}_{node.end_byte}"
        short_hash = hashlib.md5(unique_str.encode()).hexdigest()[:8]
        block_id = f"blk_{short_hash}"

        self.block_registry[block_id] = {
            "file_path": file_path,
            "start_byte": node.start_byte,
            "end_byte": node.end_byte,
            "type": node.type,
        }
        return block_id

    def generate_skeleton(self, file_path):
        source_code = self._read_file(file_path)
        source_bytes = bytes(source_code, "utf8")

        tree = self.parser.parse(source_bytes)
        cursor = tree.walk()

        output = []
        self._walk_node(cursor, source_bytes, output, indent=0, file_path=file_path)
        return "\n".join(output)

    def _walk_node(self, cursor, source_bytes, output, indent, file_path):
        node = cursor.node
        node_type = node.type
        prefix = "    " * indent

        if node_type in ["module", "block"]:
            self._walk_children(cursor, source_bytes, output, indent, file_path)

        elif node_type in ["function_definition", "class_definition"]:
            sig = self._extract_signature(node, source_bytes)

            if node_type == "function_definition":
                block_id = self._generate_block_id(file_path, node)
                output.append(f"{prefix}{sig} # [Expand: {block_id}]")
            else:
                output.append(f"{prefix}{sig}")

            self._extract_docstring(node, source_bytes, output, indent + 1)

            if node_type == "class_definition":
                self._walk_children(cursor, source_bytes, output, indent + 1, file_path)

        elif node_type in ["import_statement", "import_from_statement"]:
            output.append(f"{prefix}{self._get_text(node, source_bytes)}")

    def _walk_children(self, cursor, source_bytes, output, indent, file_path):
        if cursor.goto_first_child():
            while True:
                self._walk_node(cursor, source_bytes, output, indent, file_path)
                if not cursor.goto_next_sibling():
                    break
            cursor.goto_parent()

    def expand_block(self, block_id, max_lines=10):
        if block_id not in self.block_registry:
            return f"Error: Block {block_id} not found."

        block_info = self.block_registry[block_id]
        file_path = block_info["file_path"]

        source_code = self._read_file(file_path)
        source_bytes = bytes(source_code, "utf8")

        start = block_info["start_byte"]
        end = block_info["end_byte"]

        raw_text = source_bytes[start:end].decode("utf8")
        lines = raw_text.splitlines()

        # If it's short enough, just hand the model the exact code
        if len(lines) <= max_lines:
            return raw_text

        # Else, re-parse to isolate the node
        tree = self.parser.parse(source_bytes)
        target_node = tree.root_node.descendant_for_byte_range(start, end)

        output = [f"# --- Large block expanded: {block_id} ---"]

        if target_node.type == "function_definition":
            sig = self._extract_signature(target_node, source_bytes)
            output.append(sig)
            body = target_node.child_by_field_name("body")
            if body:
                self._walk_inner_block(
                    body.walk(), source_bytes, output, indent=1, file_path=file_path
                )
        else:
            self._walk_inner_block(
                target_node.walk(), source_bytes, output, indent=0, file_path=file_path
            )

        return "\n".join(output)

    def _walk_inner_block(self, cursor, source_bytes, output, indent, file_path):
        node = cursor.node
        prefix = "    " * indent

        # Nodes that have a header and an inner block we want to fold
        control_structures = [
            "if_statement",
            "for_statement",
            "while_statement",
            "try_statement",
            "with_statement",
            "match_statement",
            "elif_clause",
            "else_clause",
            "except_clause",
            "finally_clause",
            "case_clause",
        ]

        if node.type in control_structures:
            block_node = None
            for child in node.children:
                if child.type == "block":
                    block_node = child
                    break

            if block_node:
                header_bytes = source_bytes[node.start_byte : block_node.start_byte]
                header = header_bytes.decode("utf8").strip()
                clean_header = " ".join(
                    header.split()
                )

                inner_block_id = self._generate_block_id(file_path, block_node)
                output.append(f"{prefix}{clean_header} # [Expand: {inner_block_id}]")

                # Explicitly traverse into continuation clauses
                if cursor.goto_first_child():
                    while True:
                        if cursor.node.type in [
                            "elif_clause",
                            "else_clause",
                            "except_clause",
                            "finally_clause",
                        ]:
                            # Process these at the same indentation level
                            self._walk_inner_block(
                                cursor, source_bytes, output, indent, file_path
                            )
                        if not cursor.goto_next_sibling():
                            break
                    cursor.goto_parent()
                return

        elif node.type in [
            "expression_statement",
            "assignment",
            "return_statement",
            "pass_statement",
            "break_statement",
            "continue_statement",
        ]:
            text = self._get_text(node, source_bytes)
            for line in text.splitlines():
                output.append(f"{prefix}{line.strip()}")
            return

        # Default traversal for anything else
        if cursor.goto_first_child():
            while True:
                next_indent = indent + 1 if node.type == "block" else indent
                self._walk_inner_block(
                    cursor, source_bytes, output, next_indent, file_path
                )
                if not cursor.goto_next_sibling():
                    break
            cursor.goto_parent()

    def _extract_signature(self, node, source_bytes):
        body = node.child_by_field_name("body")
        if body:
            sig_bytes = source_bytes[node.start_byte : body.start_byte]
            sig = sig_bytes.decode("utf8").strip()
            return sig.rstrip(":").strip() + ":"
        return self._get_text(node, source_bytes)

    def _extract_docstring(self, node, source_bytes, output, indent):
        body = node.child_by_field_name("body")
        if body:
            for child in body.children:
                if (
                    child.type == "expression_statement"
                    and child.children[0].type == "string"
                ):
                    doc = self._get_text(child.children[0], source_bytes)
                    if len(doc) > 100:
                        doc = doc[:97] + '..."'
                    output.append(f"{'    ' * indent}{doc}")
                    return
                if child.type == "comment":
                    continue
                break


if __name__ == "__main__":
    skeletonizer = CodeSkeletonizer()
    print("--- High Level Skeleton ---")
    skel = skeletonizer.generate_skeleton("skeletonizer.py")
    print(skel)

    print("\n--- Deepened Block ---")
    print(skeletonizer.expand_block("blk_70ba3acc"))
