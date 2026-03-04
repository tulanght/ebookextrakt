import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

# Add src to the sys path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from extract_app.core.pdf_parser import parse_pdf, _SKIP_SPLIT_PATTERNS

class MockDocument:
    def __init__(self, toc, page_count=10, metadata=None):
        self.toc = toc
        self.page_count = page_count
        self.metadata = metadata or {'title': 'Mock PDF', 'author': 'Test'}
        self.pages_loaded = set()

    def get_toc(self):
        return self.toc

    def load_page(self, page_num):
        self.pages_loaded.add(page_num)
        mock_page = MagicMock()
        
        # We need to simulate the text heuristic if it gets called, or normal text extraction.
        # But for testing `level_nodes` hierarchy, we want to bypass heuristics to focus on hierarchy,
        # or we return empty blocks so heuristics return [] and it falls back to basic structuring.
        # Let's return some text
        mock_page.get_text.return_value = "Mock text content for page " + str(page_num)
        # Mock cover extraction attempt
        mock_page.get_images.return_value = []
        return mock_page

    def extract_image(self, xref):
        return None

    def close(self):
        pass

class TestPdfParserHierarchy(unittest.TestCase):
    @patch('extract_app.core.pdf_parser.fitz.open')
    @patch('extract_app.core.pdf_parser._extract_chapter_with_heuristics')
    @patch('extract_app.core.pdf_parser._extract_flat_chapter')
    def test_nested_toc(self, mock_flat, mock_heuristic, mock_fitz_open):
        """Test that a 3-level ToC is parsed into a proper tree."""
        # Simulated ToC: [level, title, page_number]
        toc = [
            [1, "Chapter 1", 1],
            [2, "Subchapter 1.1", 2],
            [2, "Subchapter 1.2", 3],
            [3, "Sub-subchapter 1.2.1", 4],
            [1, "Chapter 2", 5],
        ]
        mock_doc = MockDocument(toc, page_count=10)
        mock_fitz_open.return_value = mock_doc
        
        # Make the heuristic and flat extractors just return a simple article object representing the section
        # We need them to return valid sub_articles so `parse_pdf` can attach them to level_nodes
        mock_heuristic.side_effect = lambda doc, start_page, end_page, title, temp_dir, logger=None: [
            {'title': title, 'content': [], 'children': []}
        ]
        
        results = parse_pdf("dummy.pdf")
        content_tree = results.get('content', [])
        
        # We should have 2 root chapters: "Chapter 1" and "Chapter 2"
        self.assertEqual(len(content_tree), 2)
        self.assertEqual(content_tree[0]['title'], "Chapter 1")
        self.assertEqual(content_tree[1]['title'], "Chapter 2")
        
        # Chapter 1 should have 2 children
        chap1_children = content_tree[0]['children']
        self.assertEqual(len(chap1_children), 2)
        self.assertEqual(chap1_children[0]['title'], "Subchapter 1.1")
        self.assertEqual(chap1_children[1]['title'], "Subchapter 1.2")
        
        # Subchapter 1.2 should have 1 child
        subchap12_children = chap1_children[1]['children']
        self.assertEqual(len(subchap12_children), 1)
        self.assertEqual(subchap12_children[0]['title'], "Sub-subchapter 1.2.1")
        
        # Chapter 2 should have 0 children
        chap2_children = content_tree[1]['children']
        self.assertEqual(len(chap2_children), 0)

    @patch('extract_app.core.pdf_parser.fitz.open')
    @patch('extract_app.core.pdf_parser._extract_chapter_with_heuristics')
    @patch('extract_app.core.pdf_parser._extract_flat_chapter')
    def test_discontinuous_levels(self, mock_flat, mock_heuristic, mock_fitz_open):
        """Test a badly formatted ToC where it jumps from level 1 to level 3."""
        toc = [
            [1, "Chapter 1", 1],
            [3, "Badly Formatted Subchapter", 2],  # Jumps from 1 to 3
            [1, "Chapter 2", 3],
        ]
        mock_doc = MockDocument(toc, page_count=5)
        mock_fitz_open.return_value = mock_doc
        
        mock_heuristic.side_effect = lambda doc, start, end, title, td, logger=None: [{'title': title, 'content': [], 'children': []}]
        
        results = parse_pdf("dummy.pdf")
        content_tree = results.get('content', [])
        
        self.assertEqual(len(content_tree), 2)
        
        # Badly formatted subchapter should be attached to Chapter 1 (level 1), 
        # since it fell back up the tree looking for the closest parent.
        chap1 = content_tree[0]
        self.assertEqual(len(chap1['children']), 1)
        self.assertEqual(chap1['children'][0]['title'], "Badly Formatted Subchapter")


if __name__ == '__main__':
    unittest.main()
