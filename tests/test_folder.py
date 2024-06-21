import unittest
import os
from unittest.mock import patch, MagicMock
from DocParser.vrdu.preprocess import replace_figures_in_folders

class TestGeneratePngFigure(unittest.TestCase):
    def setUp(self):
        # Simulate image files
        self.image_files = {
            "file1": "dir1/file1.eps",
            "file2": "dir/dir2/file2.png",
            "file3": "dir1/file3.jpg",
            "file4": "file4.jpeg",
            "file5": "dir/dir2/dir5/file5.ps",
            "file6": "dir/dir2/dir5/file6.pdf"
        }

    @patch('vrdu.utils.convert_eps_image_to_pdf_image')
    @patch('vrdu.utils.convert_pdf_figure_to_png_image')
    @patch('os.remove')
    def test_png_generation(self, mock_os_remove, mock_convert_pdf_to_png, mock_convert_eps_to_pdf):

        # Mock os.remove to do nothing
        mock_os_remove.side_effect = lambda x: None

        replace_figures_in_folders(self.image_files)

        # Test the number of times the file conversion function is called
        self.assertEqual(mock_convert_eps_to_pdf.call_count, 2)
        self.assertEqual(mock_convert_pdf_to_png.call_count, 3)
