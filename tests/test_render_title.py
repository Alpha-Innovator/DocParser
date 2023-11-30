import unittest
import unittest.mock


from vrdu.renderer import Renderer


class TestTitle(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_file_content1 = (
            """\\documentclass{article}\\begin{document}\\end{document}"""
        )
        self.mock_file_content2 = """\\documentclass{article}\\title{This is a title}\\begin{document}\\maketitle\\end{document}"""
        self.mock_file_content3 = """\\documentclass{article}\\title{This is a title}\\title{This is anotheter title}\\begin{document}\\maketitle\\end{document}"""
        self.mock_file_content4 = """\\documentclass{article}\\icmltitle{This is a title}\\begin{document}\\maketitle\\end{document}"""
        self.renderer = Renderer()

    def test_no_title(self):
        with unittest.mock.patch(
            "builtins.open",
            new=unittest.mock.mock_open(read_data=self.mock_file_content1),
            create=True,
        ) as file_mock:
            self.renderer.render_title(file_mock)
            file_mock.assert_called_with(file_mock)

    def test_one_title(self):
        with unittest.mock.patch(
            "builtins.open",
            new=unittest.mock.mock_open(read_data=self.mock_file_content2),
            create=True,
        ) as file_mock:
            self.renderer.render_title(file_mock)
            file_mock.assert_called_with(file_mock, "w")
            file_mock().write.assert_called_with(
                """\\documentclass{article}\\title{\\textcolor{PaperTitle_color}{This is a title}}\\begin{document}\\maketitle\\end{document}"""
            )

    def test_two_title(self):
        with unittest.mock.patch(
            "builtins.open",
            new=unittest.mock.mock_open(read_data=self.mock_file_content3),
            create=True,
        ) as file_mock:
            self.assertRaises(ValueError, self.renderer.render_title, file_mock)

    def test_unusual_title(self):
        with unittest.mock.patch(
            "builtins.open",
            new=unittest.mock.mock_open(read_data=self.mock_file_content4),
            create=True,
        ) as file_mock:
            self.renderer.render_title(file_mock)
            file_mock.assert_called_with(file_mock)
