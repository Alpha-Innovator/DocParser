import unittest
import os
from unittest.mock import patch, MagicMock


from DocParser.vrdu.preprocess import generate_png_figure


class TestGeneratePngFigure(unittest.TestCase):
    @patch("os.path.dirname", return_value="/mocked/dir/")
    @patch("os.walk")
    @patch("DocParser.vrdu.utils.convert_pdf_figure_to_png_image")
    def test_single_pdf_generation(self, mock_save, mock_walk, mock_dirname):
        mocked_file = "/mocked/dir/original.tex"
        mock_walk.return_value = [
            ("/mocked/dir/", ["dir1", "dir2"], ["file1.txt", "file2.csv"]),
            ("/mocked/dir/dir1", [], ["file3.json"]),
            ("/mocked/dir/dir2", [], ["file4.pdf"]),
        ]
        generate_png_figure(mocked_file)
        # mock_dirname.assert_called_once_with(mocked_file)

        mock_walk.assert_called_once_with("/mocked/dir/")

        mock_save.assert_called_once_with(
            "/mocked/dir/dir2/file4.pdf", "/mocked/dir/dir2/file4.png"
        )
