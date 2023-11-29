import unittest
import unittest.mock


from vrdu.renderer import Renderer


class TestFootnote(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_file_content1 = (
            """\\documentclass{article}\\begin{document}\\end{document}"""
        )
        self.mock_file_content2 = """\\documentclass{article}\\begin{document}\\includegraphics{figures/time_vs_dimension.png}\\end{document}"""
        self.mock_file_content3 = """\\documentclass{article}\\begin{document}\\includegraphics[width=\\columnwidth]{figures/time_vs_dimension.png}\\end{document}"""
        self.mock_file_content4 = """\\begin{figure}[ht]
            \\vskip 0.2in
            % \\begin{center}
            \\subfigure[]{\\includegraphics[width=0.48\\columnwidth]{figures/iterate_constraint.png}} 
            \\subfigure[]{\\includegraphics[width=0.48\\columnwidth]{figures/iterate_error.png}} 
            \\subfigure[]{\\includegraphics[width=0.48\\columnwidth]{figures/time_constraint.png}}
            \\subfigure[]{\\includegraphics[width=0.5\\columnwidth]{figures/time_error.png}}
            \\caption{Iteration information of SNA (red), NRFM (blue) and PDN (green). Top: $\\|\\boldsymbol\\mu^k-\\boldsymbol\\mu^*\\|_2^2$ (a) and $|\\lambda^k-\\lambda^*|^2$ (b) against iterations. Bottom: $\\|\\boldsymbol\\mu^k-\\boldsymbol\\mu^*\\|_2^2$ (c) and $|\\lambda^k-\\lambda^*|^2$  (d) against time.}
            \\label{fig:iteration_information}
            % \\end{center}
            \\vskip -0.2in
        """
        self.renderer = Renderer()

    def test_no_graphics(self):
        with unittest.mock.patch(
            "builtins.open",
            new=unittest.mock.mock_open(read_data=self.mock_file_content1),
            create=True,
        ) as file_mock:
            self.renderer.extract_graphics(file_mock)
            self.assertEqual(self.renderer.texts["Figure"], [])

    def test_one_graphic1(self):
        with unittest.mock.patch(
            "builtins.open",
            new=unittest.mock.mock_open(read_data=self.mock_file_content2),
            create=True,
        ) as file_mock:
            self.renderer.extract_graphics(file_mock)
            file_mock.assert_called_with(file_mock, "r")
            self.assertEqual(
                self.renderer.texts["Figure"],
                ["\\includegraphics{figures/time_vs_dimension.png}"],
            )

    def test_one_graphic2(self):
        with unittest.mock.patch(
            "builtins.open",
            new=unittest.mock.mock_open(read_data=self.mock_file_content3),
            create=True,
        ) as file_mock:
            self.renderer.extract_graphics(file_mock)
            file_mock.assert_called_with(file_mock, "r")
            self.assertEqual(
                self.renderer.texts["Figure"],
                [
                    "\\includegraphics[width=\\columnwidth]{figures/time_vs_dimension.png}"
                ],
            )

    def test_multiple_graphics(self):
        with unittest.mock.patch(
            "builtins.open",
            new=unittest.mock.mock_open(read_data=self.mock_file_content4),
            create=True,
        ) as file_mock:
            self.renderer.extract_graphics(file_mock)
            file_mock.assert_called_with(file_mock, "r")
            self.assertEqual(
                self.renderer.texts["Figure"],
                [
                    "\\includegraphics[width=0.48\\columnwidth]{figures/iterate_constraint.png}",
                    "\\includegraphics[width=0.48\\columnwidth]{figures/iterate_error.png}",
                    "\\includegraphics[width=0.48\\columnwidth]{figures/time_constraint.png}",
                    "\\includegraphics[width=0.5\\columnwidth]{figures/time_error.png}",
                ],
            )
