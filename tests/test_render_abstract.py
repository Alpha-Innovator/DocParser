import unittest
import unittest.mock


from vrdu.renderer import Renderer


class TestAbstract(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_file_content1 = (
            """\\documentclass{article}\\begin{document}\\end{document}"""
        )

        self.mock_file_content2 = """\\documentclass{article}\\begin{document}\\begin{abstract}\n   This is the content of abstract.\n \\end{abstract}\\end{document}"""
        self.renderer = Renderer()

    def test_no_abstract(self):
        with unittest.mock.patch(
            "builtins.open",
            new=unittest.mock.mock_open(read_data=self.mock_file_content1),
            create=True,
        ) as file_mock:
            self.renderer.render_abstract(file_mock)
            file_mock.assert_called_with(file_mock)

    def test_one_abstract(self):
        with unittest.mock.patch(
            "builtins.open",
            new=unittest.mock.mock_open(read_data=self.mock_file_content2),
            create=True,
        ) as file_mock:
            self.renderer.render_abstract(file_mock)
            file_mock.assert_called_with(file_mock, "w")
            file_mock().write.assert_called_with(
                """\\documentclass{article}\\begin{document}\\begin{abstract}\\color{Abstract_color}\n   This is the content of abstract.\n \\end{abstract}\\end{document}"""
            )
