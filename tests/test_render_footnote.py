import unittest
import unittest.mock


from DocParser.vrdu.renderer import Renderer


class TestFootnote(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_file_content1 = (
            """\\documentclass{article}\\begin{document}\\end{document}"""
        )
        self.mock_file_content2 = """\\documentclass{article}\\begin{document}\\footnote{A footnote.}\\end{document}"""
        self.mock_file_content3 = """\\documentclass{article}\\begin{document}\\footnote{\\url{A figure without list entry.}}\\end{document}"""
        self.mock_file_content4 = """\\documentclass{article}\\begin{document}\\footnote{A figure without list entry.}\\footnote{A figure without list entry.}\\end{document}"""
        self.mock_file_content5 = """\\documentclass{article}\\begin{document}Table \\ref{demo-table} has a caption:\\begin{table}[!h]\\begin{center}\\begin{tabular}{||c c c c||}  \\hline Col1 & Col2 & Col2 & Col3 \\ [0.5ex]  \\hline\\hline 1 & 6 & 87837 & 787 \\  \\hline 2 & 7 & 78 & 5415 \\ \\hline 3 & 545 & 778 & 7507 \\ \\hline 4 & 545 & 18744 & 7560 \\ \\hline 5 & 88 & 788 & 6344 \\ [1ex]  \\hline\\end{tabular}\\caption{\\label{demo-table}Your caption.\\footnote{\\url{A figure without list entry.}}\\end{center}\\end{table}\\end{document}"""
        self.mock_file_content6 = """\\documentclass{article}\\begin{document}\footnotesize $X_{n-1}^{(t)}$\\end{document}"""
        self.renderer = Renderer()

    def test_no_footnote(self):
        with unittest.mock.patch(
            "builtins.open",
            new=unittest.mock.mock_open(read_data=self.mock_file_content1),
            create=True,
        ) as file_mock:
            self.renderer.render_footnote(file_mock)
            file_mock.assert_called_with(file_mock, "w")
            file_mock().write.assert_called_with(
                """\\documentclass{article}\\begin{document}\\end{document}"""
            )

    def test_one_footnote1(self):
        with unittest.mock.patch(
            "builtins.open",
            new=unittest.mock.mock_open(read_data=self.mock_file_content2),
            create=True,
        ) as file_mock:
            self.renderer.render_footnote(file_mock)
            file_mock.assert_called_with(file_mock, "w")
            file_mock().write.assert_called_with(
                """\\documentclass{article}\\begin{document}\\footnote{{\\color{Footnote_color}A footnote.}}\\end{document}"""
            )

    def test_one_footnote2(self):
        with unittest.mock.patch(
            "builtins.open",
            new=unittest.mock.mock_open(read_data=self.mock_file_content3),
            create=True,
        ) as file_mock:
            self.renderer.render_footnote(file_mock)
            file_mock.assert_called_with(file_mock, "w")
            file_mock().write.assert_called_with(
                """\\documentclass{article}\\begin{document}\\footnote{{\\color{Footnote_color}\\url{A figure without list entry.}}}\\end{document}"""
            )

    def test_multiple_footnote(self):
        with unittest.mock.patch(
            "builtins.open",
            new=unittest.mock.mock_open(read_data=self.mock_file_content4),
            create=True,
        ) as file_mock:
            self.renderer.render_footnote(file_mock)
            file_mock.assert_called_with(file_mock, "w")
            file_mock().write.assert_called_with(
                """\\documentclass{article}\\begin{document}\\footnote{{\\color{Footnote_color}A figure without list entry.}}\\footnote{{\\color{Footnote_color}A figure without list entry.}}\\end{document}"""
            )

    def test_nested_footnote(self):
        with unittest.mock.patch(
            "builtins.open",
            new=unittest.mock.mock_open(read_data=self.mock_file_content5),
            create=True,
        ) as file_mock:
            self.renderer.render_footnote(file_mock)
            file_mock.assert_called_with(file_mock, "w")
            file_mock().write.assert_called_with(
                """\\documentclass{article}\\begin{document}Table \\ref{demo-table} has a caption:\\begin{table}[!h]\\begin{center}\\begin{tabular}{||c c c c||}  \\hline Col1 & Col2 & Col2 & Col3 \\ [0.5ex]  \\hline\\hline 1 & 6 & 87837 & 787 \\  \\hline 2 & 7 & 78 & 5415 \\ \\hline 3 & 545 & 778 & 7507 \\ \\hline 4 & 545 & 18744 & 7560 \\ \\hline 5 & 88 & 788 & 6344 \\ [1ex]  \\hline\\end{tabular}\\caption{\\label{demo-table}Your caption.\\footnote{{\\color{Footnote_color}\\url{A figure without list entry.}}}\\end{center}\\end{table}\\end{document}"""
            )

    def test_no_footnote2(self):
        with unittest.mock.patch(
            "builtins.open",
            new=unittest.mock.mock_open(read_data=self.mock_file_content6),
            create=True,
        ) as file_mock:
            self.renderer.render_footnote(file_mock)
            file_mock.assert_called_with(file_mock, "w")
            file_mock().write.assert_called_with(
                """\\documentclass{article}\\begin{document}\footnotesize $X_{n-1}^{(t)}$\\end{document}"""
            )
