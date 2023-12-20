import unittest


from vrdu.utils import extract_title_name


class TestExtractTitleName(unittest.TestCase):
    def test_title_name(self):
        self.assertEqual(extract_title_name("\\section{Name}"), "section")
        self.assertEqual(extract_title_name("\\subsection*{AnotherName}"), "subsection")
        self.assertEqual(extract_title_name("No match"), "")
        self.assertEqual(
            extract_title_name("\\subsubsection{No match}"), "subsubsection"
        )
        self.assertEqual(
            extract_title_name("\\subsubsection*{No match}"), "subsubsection"
        )
