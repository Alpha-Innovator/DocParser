import unittest
import unittest.mock


from vrdu.renderer import Renderer


class TestCaption(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_file_content1 = (
            """\\documentclass{article}\\begin{document}\\end{document}"""
        )
        self.mock_file_content2 = """\\documentclass{article}\\begin{document}\\caption{A figure without list entry.}\\end{document}"""
        self.mock_file_content3 = """\\documentclass{article}\\begin{document}\\caption[]{A figure without list entry.}\\end{document}"""
        self.mock_file_content4 = """\\documentclass{article}\\begin{document}\\caption{A figure without list entry.}\\caption{A figure without list entry.}\\end{document}"""
        self.mock_file_content5 = """\\documentclass{article}\\begin{document}Table \\ref{demo-table} has a caption:\\begin{table}[!h]\\begin{center}\\begin{tabular}{||c c c c||}  \\hline Col1 & Col2 & Col2 & Col3 \\ [0.5ex]  \\hline\\hline 1 & 6 & 87837 & 787 \\  \\hline 2 & 7 & 78 & 5415 \\ \\hline 3 & 545 & 778 & 7507 \\ \\hline 4 & 545 & 18744 & 7560 \\ \\hline 5 & 88 & 788 & 6344 \\ [1ex]  \\hline\\end{tabular}\\caption{\\label{demo-table}Your caption.}\\end{center}\\end{table}\\end{document}"""

        self.renderer = Renderer()

    def test_no_caption(self):
        with unittest.mock.patch(
            "builtins.open",
            new=unittest.mock.mock_open(read_data=self.mock_file_content1),
            create=True,
        ) as file_mock:
            self.renderer.render_caption(file_mock)
            file_mock.assert_called_with(file_mock, "w")
            file_mock().write.assert_called_with(
                """\\documentclass{article}\\begin{document}\\end{document}"""
            )

    def test_one_caption1(self):
        with unittest.mock.patch(
            "builtins.open",
            new=unittest.mock.mock_open(read_data=self.mock_file_content2),
            create=True,
        ) as file_mock:
            self.renderer.render_caption(file_mock)
            file_mock.assert_called_with(file_mock, "w")
            file_mock().write.assert_called_with(
                """\\documentclass{article}\\begin{document}\\caption{{\\color{Caption_color}A figure without list entry.}}\\end{document}"""
            )

    def test_one_caption2(self):
        with unittest.mock.patch(
            "builtins.open",
            new=unittest.mock.mock_open(read_data=self.mock_file_content3),
            create=True,
        ) as file_mock:
            self.renderer.render_caption(file_mock)
            file_mock.assert_called_with(file_mock, "w")
            file_mock().write.assert_called_with(
                """\\documentclass{article}\\begin{document}\\caption[]{{\\color{Caption_color}A figure without list entry.}}\\end{document}"""
            )

    def test_multiple_caption(self):
        with unittest.mock.patch(
            "builtins.open",
            new=unittest.mock.mock_open(read_data=self.mock_file_content4),
            create=True,
        ) as file_mock:
            self.renderer.render_caption(file_mock)
            file_mock.assert_called_with(file_mock, "w")
            file_mock().write.assert_called_with(
                """\\documentclass{article}\\begin{document}\\caption{{\\color{Caption_color}A figure without list entry.}}\\caption{{\\color{Caption_color}A figure without list entry.}}\\end{document}"""
            )

    def test_table_caption(self):
        with unittest.mock.patch(
            "builtins.open",
            new=unittest.mock.mock_open(read_data=self.mock_file_content5),
            create=True,
        ) as file_mock:
            self.renderer.render_caption(file_mock)
            file_mock.assert_called_with(file_mock, "w")
            file_mock().write.assert_called_with(
                """\\documentclass{article}\\begin{document}Table \\ref{demo-table} has a caption:\\begin{table}[!h]\\begin{center}\\begin{tabular}{||c c c c||}  \\hline Col1 & Col2 & Col2 & Col3 \\ [0.5ex]  \\hline\\hline 1 & 6 & 87837 & 787 \\  \\hline 2 & 7 & 78 & 5415 \\ \\hline 3 & 545 & 778 & 7507 \\ \\hline 4 & 545 & 18744 & 7560 \\ \\hline 5 & 88 & 788 & 6344 \\ [1ex]  \\hline\\end{tabular}\\caption{{\\color{Caption_color}\\label{demo-table}Your caption.}}\\end{center}\\end{table}\\end{document}"""
            )
