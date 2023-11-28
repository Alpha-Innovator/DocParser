import unittest
import unittest.mock


from vrdu.renderer import Renderer


class TestHyperref(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_file_content1 = (
            r"""\\documentclass{article}\\begin{document}\\end{document}"""
        )
        self.mock_file_content2 = r"""\\documentclass{article}\\usepackage{hyperref}\\begin{document}\\end{document}"""
        self.mock_file_content3 = r"""\\documentclass{article}\\usepackage[color_links=true]{hyperref}\\begin{document}\\end{document}"""
        self.mock_file_content4 = r"""\\documentclass{article}\\usepackage[color_links=true]{hyperref}\\usepackage{amsmath}\\begin{document}\\end{document}"""
        self.renderer = Renderer()

    def test1(self):
        with unittest.mock.patch(
            "builtins.open",
            new=unittest.mock.mock_open(read_data=self.mock_file_content1),
            create=True,
        ) as file_mock:
            self.renderer.remove_hyperref_color(file_mock)
            file_mock.assert_called_with(file_mock, "w")
            file_mock().write.assert_called_with(
                r"""\\documentclass{article}\\begin{document}\\end{document}"""
            )

    def test2(self):
        with unittest.mock.patch(
            "builtins.open",
            new=unittest.mock.mock_open(read_data=self.mock_file_content2),
            create=True,
        ) as file_mock:
            self.renderer.remove_hyperref_color(file_mock)
            file_mock.assert_called_with(file_mock, "w")
            file_mock().write.assert_called_with(
                r"""\\documentclass{article}\\usepackage{hyperref}\\hypersetup{colorlinks=false}\\begin{document}\\end{document}"""
            )

    def test3(self):
        with unittest.mock.patch(
            "builtins.open",
            new=unittest.mock.mock_open(read_data=self.mock_file_content3),
            create=True,
        ) as file_mock:
            self.renderer.remove_hyperref_color(file_mock)
            file_mock.assert_called_with(file_mock, "w")
            file_mock().write.assert_called_with(
                r"""\\documentclass{article}\\usepackage[color_links=true]{hyperref}\\hypersetup{colorlinks=false}\\begin{document}\\end{document}"""
            )

    def test4(self):
        with unittest.mock.patch(
            "builtins.open",
            new=unittest.mock.mock_open(read_data=self.mock_file_content4),
            create=True,
        ) as file_mock:
            self.renderer.remove_hyperref_color(file_mock)
            file_mock.assert_called_with(file_mock, "w")
            file_mock().write.assert_called_with(
                r"""\\documentclass{article}\\usepackage[color_links=true]{hyperref}\\usepackage{amsmath}\\hypersetup{colorlinks=false}\\begin{document}\\end{document}"""
            )
