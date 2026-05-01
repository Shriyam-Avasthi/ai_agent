import os
import re
import shutil
import sys
import tempfile
import unittest

from functions.edit_file import edit_file
from functions.expand_block import expand_block
from functions.get_file_skeleton import get_file_skeleton
from functions.list_directory import list_directory
from functions.write_file import write_file

VERBOSE = False


class TestWorkspaceTools(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        # Create a dummy python file for AST parsing
        self.test_file_name = "main_dummy.py"
        self.test_file_path = os.path.join(self.test_dir, self.test_file_name)
        with open(self.test_file_path, "w", encoding="utf-8") as f:
            f.write("def add(a, b):\n    return a + b\n")

        # Create a sub-directory to test list_directory
        os.makedirs(os.path.join(self.test_dir, "pkg"))
        with open(os.path.join(self.test_dir, "pkg", "__init__.py"), "w") as f:
            f.write("")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_list_directory(self):
        tree = list_directory(self.test_dir)
        if VERBOSE:
            print(f"[Tree Output]\n{tree}")

        self.assertIn("main_dummy.py", tree)
        self.assertIn("pkg", tree)

    def test_skeleton_and_expand_pipeline(self):
        skeleton = get_file_skeleton(self.test_dir, self.test_file_name)
        if VERBOSE:
            print(f"[Skeleton Output]\n{skeleton}")

        self.assertIn("def add(a, b):", skeleton)
        self.assertIn("[Expand: blk_", skeleton)

        # Extract the dynamic Block ID using Regex
        match = re.search(r"\[Expand: (blk_[a-f0-9]+)\]", skeleton)
        self.assertIsNotNone(match, "Failed to find Block ID in skeleton")
        block_id = match.group(1)  # type: ignore

        # Expand the Block
        expanded_code = expand_block(block_id)
        if VERBOSE:
            print(f"\n[Expanded Block {block_id}]\n{expanded_code}")

        self.assertIn("return a + b", expanded_code)

    def test_edit_file_exact_match(self):
        search_block = "def add(a, b):\n    return a + b"
        replace_block = "def add(a, b):\n    return float(a) + float(b)"

        result = edit_file(
            self.test_dir, self.test_file_name, search_block, replace_block
        )
        if VERBOSE:
            print(f"[Edit Result]: {result}")

        self.assertIn("Success", result)

        with open(self.test_file_path, "r", encoding="utf-8") as f:
            updated_content = f.read()

        if VERBOSE:
            print(f"[File System Check]\n{updated_content}")
        self.assertIn("return float(a) + float(b)", updated_content)
        self.assertNotIn("return a + b", updated_content)

    def test_path_traversal_security(self):
        # Test out-of-bounds skeleton generation
        skeleton_err = get_file_skeleton(self.test_dir, "../main.py")
        if VERBOSE:
            print(f"[Path Escape Skeleton]: {skeleton_err}")
        self.assertIn("Error", skeleton_err)

        # Test out-of-bounds file editing
        edit_err = edit_file(self.test_dir, "/tmp/hack.py", "a", "b")
        if VERBOSE:
            print(f"[Path Escape Edit]: {edit_err}")
        self.assertIn("Error", edit_err)

    def test_write_file_creation(self):
        new_file_name = "lorem_test.txt"
        test_string = "Hello, Agentic World!"

        result = write_file(self.test_dir, new_file_name, test_string)
        if VERBOSE:
            print(f"[Write Target] write_file returned: {result}")

        with open(
            os.path.join(self.test_dir, new_file_name), "r", encoding="utf-8"
        ) as f:
            actual_content = f.read()

        if VERBOSE:
            print(f"[File System] Actual file content contains: {actual_content}")
        self.assertEqual(actual_content, test_string)


if __name__ == "__main__":
    if "-v" in sys.argv or "--verbose" in sys.argv:
        VERBOSE = True
        if "-v" in sys.argv:
            sys.argv.remove("-v")
        if "--verbose" in sys.argv:
            sys.argv.remove("--verbose")

    unittest.main(verbosity=2 if VERBOSE else 1)
