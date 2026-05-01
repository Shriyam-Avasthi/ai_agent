import os
import sys

from fileEditor import FileEditor
from semanticSearcher import SemanticSearcher
from skeletonizer import CodeSkeletonizer

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

skeletonizer_instance = CodeSkeletonizer()
editor_instance = FileEditor()
searcher_instance = SemanticSearcher(skeletonizer_instance)
