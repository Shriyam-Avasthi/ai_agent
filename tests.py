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
from functions.get_file_content import get_file_content
from functions.get_files_info import get_files_info
from functions.manage_scratchpad import manage_scratchpad
from functions.run_python_file import run_python_file

VERBOSE = False


class TestWorkspaceTools(unittest.TestCase):
    def setUp(self):
        # Use the outputs directory which is the only writable path inside the bwrap sandbox
        self.test_dir = os.path.join(os.getcwd(), "outputs")
        os.makedirs(self.test_dir, exist_ok=True)
        # Create a dummy python file for AST parsing
        self.test_file_name = "main_dummy.py"
        self.test_file_path = os.path.join(self.test_dir, self.test_file_name)
        with open(self.test_file_path, "w", encoding="utf-8") as f:
            f.write("def add(a, b):\n    return a + b\n")

        # Create a sub-directory to test list_directory
        os.makedirs(os.path.join(self.test_dir, "pkg"), exist_ok=True)
        with open(os.path.join(self.test_dir, "pkg", "__init__.py"), "w") as f:
            f.write("")

    def tearDown(self):
        # Use a safe cleanup that doesn't try to remove the 'outputs' directory itself
        if hasattr(self, 'test_dir') and self.test_dir == os.path.join(os.getcwd(), "outputs"):
            for filename in os.listdir(self.test_dir):
                file_path = os.path.join(self.test_dir, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f"Failed to delete {file_path}. Reason: {e}")
        else:
            if hasattr(self, 'test_dir'):
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

    def test_get_file_content(self):
        content = get_file_content(self.test_dir, self.test_file_name)
        self.assertIn("def add(a, b):", content)

    def test_get_files_info(self):
        info = get_files_info(self.test_dir)
        self.assertIn(self.test_file_name, info)
        self.assertIn("pkg", info)

    def test_manage_scratchpad(self):
        # Test append
        res_append = manage_scratchpad(self.test_dir, "append", "Step 1")
        self.assertIn("Content appended", res_append)
        
        # Test update
        res_update = manage_scratchpad(self.test_dir, "update", "Updated Step")
        self.assertIn("Scratchpad updated", res_update)
        
        # Test clear
        res_clear = manage_scratchpad(self.test_dir, "clear")
        self.assertIn("Scratchpad cleared", res_clear)

    def test_run_python_file(self):
        # Normal case: basic execution
        script_name = "test_run.py"
        script_content = "print('Hello from run_python_file')"
        write_file(self.test_dir, script_name, script_content)
        result = run_python_file(self.test_dir, script_name)
        self.assertIn("Hello from run_python_file", result)

        # Normal case: execution with arguments
        arg_script_name = "test_args.py"
        arg_script_content = "import sys\nprint(f'Args: {sys.argv[1:]}')"
        write_file(self.test_dir, arg_script_name, arg_script_content)
        result_args = run_python_file(self.test_dir, arg_script_name, args=["arg1", "arg2"])
        self.assertIn("Args: ['arg1', 'arg2']", result_args)

        # Edge case: non-existent file
        result_none = run_python_file(self.test_dir, "non_existent.py")
        self.assertIn("Error", result_none)

        # Edge case: script that fails
        fail_script_name = "test_fail.py"
        fail_script_content = "raise Exception('Test Exception')"
        write_file(self.test_dir, fail_script_name, fail_script_content)
        result_fail = run_python_file(self.test_dir, fail_script_name)
        self.assertIn("Test Exception", result_fail)


    def test_edit_file_no_match(self):
        result = edit_file(self.test_dir, self.test_file_name, "non-existent text", "replace text")
        self.assertIn("Error", result)

    def test_get_file_skeleton_non_existent(self):
        result = get_file_skeleton(self.test_dir, "ghost.py")
        self.assertIn("Error", result)


if __name__ == "__main__":
    if "-v" in sys.argv or "--verbose" in sys.argv:
        VERBOSE = True
        if "-v" in sys.argv:
            sys.argv.remove("-v")
        if "--verbose" in sys.argv:
            sys.argv.remove("--verbose")

    unittest.main(verbosity=2 if VERBOSE else 1)
