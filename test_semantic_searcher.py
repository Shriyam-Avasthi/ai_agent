import unittest
from unittest.mock import MagicMock, patch
import subprocess

from semanticSearcher import SemanticSearcher 

class TestSemanticSearcher(unittest.TestCase):
    def setUp(self):
        self.mock_skeletonizer = MagicMock()
        self.searcher = SemanticSearcher(self.mock_skeletonizer)

    @patch("subprocess.run")
    def test_search_timeout(self, mock_run):
        """Test behavior when ripgrep takes too long."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="rg", timeout=10)
        
        result = self.searcher.search_codebase("/fake/dir", "pattern")
        self.assertEqual(result, "Error: Search timed out.")

    @patch("subprocess.run")
    def test_no_matches_found(self, mock_run):
        """Test behavior when ripgrep runs successfully but finds nothing."""
        mock_run.return_value = MagicMock(stdout="", text=True)
        
        result = self.searcher.search_codebase("/fake/dir", "pattern")
        self.assertEqual(result, "No matches found for 'pattern'.")

    @patch("os.path.relpath")
    @patch("subprocess.run")
    def test_successful_search_and_ast_walk(self, mock_run, mock_relpath):
        """Test a successful search, simulating the AST parsing and Trie building."""
        
        mock_relpath.return_value = "src/auth.py"

        fake_rg_output = "src/auth.py:42:        if user_id == 0:"
        mock_run.return_value = MagicMock(stdout=fake_rg_output, text=True)

        self.mock_skeletonizer._read_file.return_value = "def check_user(user_id):\n    if user_id == 0:\n        pass"

        mock_func_node = MagicMock()
        mock_func_node.type = "function_definition"
        mock_func_node.parent = None  
        
        mock_leaf_node = MagicMock()
        mock_leaf_node.type = "if_statement" 
        mock_leaf_node.parent = mock_func_node 

        mock_tree = MagicMock()
        mock_tree.root_node.descendant_for_point_range.return_value = mock_leaf_node
        self.mock_skeletonizer.parser.parse.return_value = mock_tree

        self.mock_skeletonizer._extract_signature.return_value = "def check_user(self, user_id):"
        self.mock_skeletonizer._generate_block_id.return_value = "block_123"

        result = self.searcher.search_codebase("/fake/dir", "user_id")

        expected_output = (
            "src/auth.py\n"
            "    def check_user(self, user_id): # [Expand: block_123]\n"
            "            --> Line 42: if user_id == 0:"
        )
        
        self.assertEqual(result, expected_output)
        self.mock_skeletonizer._read_file.assert_called_once_with("src/auth.py")

    @patch("subprocess.run")
    def test_parser_exception_graceful_handling(self, mock_run):
        """Test that if the AST parser crashes on a file, it skips gracefully without breaking the whole search."""
        mock_run.return_value = MagicMock(stdout="src/bad_file.py:10: match", text=True)
        
        # Force the parser to throw an exception
        self.mock_skeletonizer.parser.parse.side_effect = Exception("Parse failed")
        
        result = self.searcher.search_codebase("/fake/dir", "pattern")
        self.assertEqual(result, "")

if __name__ == "__main__":
    unittest.main()
