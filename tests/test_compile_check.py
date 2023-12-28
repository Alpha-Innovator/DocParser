import unittest
import unittest.mock
import os

from vrdu.utils import compile_check


class TestGraphics(unittest.TestCase):
    def test_equation1(self):
        self.assertEqual(compile_check(r"\begin{equation}a \end{equation}"), True)

        temp_files = [file for file in os.listdir(".") if file.startswith("temp")]
        self.assertEqual(len(temp_files), 0)
