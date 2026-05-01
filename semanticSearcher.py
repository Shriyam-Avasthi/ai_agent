import subprocess
import os
from collections import defaultdict

import skeletonizer

class SemanticSearcher:
    def __init__(self, skeletonizer_instance):
        self.skeletonizer = skeletonizer_instance

    def search_codebase(self, working_dir: str, regex_pattern: str) -> str:
        """Runs ripgrep, maps to AST, and consolidates into a hierarchical tree."""
        cmd = ["rg", "-n", "-t", "py", regex_pattern, working_dir]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        except FileNotFoundError:
            return "Error: 'rg' (ripgrep) is not installed."
        except subprocess.TimeoutExpired:
            return "Error: Search timed out."
            
        if not result.stdout:
            return f"No matches found for '{regex_pattern}'."

        matches_by_file = defaultdict(list)
        for line in result.stdout.strip().split('\n'):
            parts = line.split(':', 2)
            if len(parts) >= 3:
                matches_by_file[parts[0]].append((int(parts[1]) - 1, parts[2]))

        output_blocks = []

        for file_path, matches in matches_by_file.items():
            try:
                source_code = self.skeletonizer._read_file(file_path)
                source_bytes = bytes(source_code, "utf8")
                tree = self.skeletonizer.parser.parse(source_bytes)
            except Exception:
                continue

            # Trie to hold the consolidated tree for this file
            file_tree = {}

            for line_num, text in matches:
                path = self._build_path(tree, source_bytes, file_path, line_num)
                
                current_level = file_tree
                for step in path:
                    if step not in current_level:
                        current_level[step] = {}
                    current_level = current_level[step]
                
                # Store the actual match at the leaf
                if "_matches_" not in current_level:
                    current_level["_matches_"] = []
                current_level["_matches_"].append(f"Line {line_num + 1}: {text.strip()}")

            rel_path = os.path.relpath(file_path, working_dir)
            formatted_tree = [f"{rel_path}"]
            self._format_trie(file_tree, formatted_tree, indent=1)
            
            output_blocks.append("\n".join(formatted_tree))

        return "\n\n".join(output_blocks)

    def _build_path(self, tree, source_bytes, file_path, line_num):
        """Walks UP the AST from a match, returning a list of (header, block_id) tuples."""
        node = tree.root_node.descendant_for_point_range((line_num, 0), (line_num, 1000))
        if not node:
            return []

        structural_nodes = [
            "function_definition", "class_definition", "if_statement", 
            "for_statement", "while_statement", "try_statement", "with_statement"
        ]
        
        parents = []
        while node:
            if node.type in structural_nodes:
                target_node_for_id = node
                header_text = ""
                
                if node.type in ["function_definition", "class_definition"]:
                    header_text = self.skeletonizer._extract_signature(node, source_bytes)
                else:
                    for child in node.children:
                        if child.type == "block":
                            target_node_for_id = child
                            header_bytes = source_bytes[node.start_byte : child.start_byte]
                            header_text = " ".join(header_bytes.decode("utf8").strip().split())
                            break
                
                if header_text:
                    block_id = self.skeletonizer._generate_block_id(file_path, target_node_for_id)
                    # Store as tuple so it's hashable for the Trie dictionary
                    parents.append((header_text, block_id))
                    
            node = node.parent
            
        parents.reverse()
        return parents

    def _format_trie(self, current_level, output_list, indent):
        """Recursively formats the Prefix Tree into the requested hierarchy."""
        prefix = "    " * indent
        
        for key, subtree in current_level.items():
            if key == "_matches_":
                continue
            header, block_id = key
            output_list.append(f"{prefix}{header} # [Expand: {block_id}]")
            self._format_trie(subtree, output_list, indent + 1)
            
        if "_matches_" in current_level:
            match_prefix = "    " * (indent + 1)
            for match in current_level["_matches_"]:
                output_list.append(f"{match_prefix}--> {match}")


if __name__ == "__main__":
    skeletonizer_instance = skeletonizer.CodeSkeletonizer()
    semanticSearcher = SemanticSearcher(skeletonizer_instance)

