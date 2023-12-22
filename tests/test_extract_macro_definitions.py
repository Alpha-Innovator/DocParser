import unittest
import unittest.mock

from vrdu.utils import extract_macro_definitions


class TestExtractMacroDefinitions(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_file_content1 = (
            """\\documentclass{article}\\begin{document}\\end{document}"""
        )
        self.mock_file_content2 = r"""\documentclass{article}
            \newcommand{\Sin}{\mathrm{sin}\,\theta}
            \newcommand{\Cos}{\mathrm{cos}\,\theta}
            \newcommand{\Tan}{\mathrm{tan}\,\theta}
            \begin{document}  
                \[ \Tan = \frac{\Sin}{\Cos} \]  \[ (\Sin)^2 + (\Cos)^2 =1 \] 
                \[ \cot\theta = \frac{\Cos}{\Sin} \]
            \end{document}
            """
        self.mock_file_content3 = r"""\documentclass{article}
            \newcommand{\trig}[1]{\mathrm{\#1}\,\theta}
            \begin{document}
                \[ \trig{sin},\,\trig{cos},\,\trig{tan} \]
                \[ \trig{tan} = \frac{\trig{sin}}{\trig{cos}} \]
                \[ \trig{sin^2} + \trig{cos^2} =1 \]
                \[ \int \frac{\trig{cos^3}}{1+\trig{sin^2}}d\theta \]
            \end{document}
            """
        self.mock_file_content4 = r"""\documentclass{article}
            \newcommand{\trig}[2]{\mathrm{\#1}\left(\#2\right)}
            \newcommand{\Int}[2]{\int_{\#2}^{\#1}}
            \begin{document}
                \[ \int\frac{du}{\sqrt{a^2 + u^2}}=\trig{sin^{\!-1}}{\frac{u}{a}} + C \]
                \[ \int\trig{sec}{\frac{a}{x}}dx = \frac{1}{a} \log\trig{tan}{\frac{\pi}{4}+ \frac{a}{2x}} + C \]
                \[ \Int{a}{b}f(x)dx = \sum_{k=1}^n \trig{sin}{5+\frac{3k}{n}} \]
                \[ \Int{b}{a}f(x)dx = \lim_{n \to \infty} \sum_{i=1}^{n}f(x_i)\delta x \]
            \end{document}
            """
        self.mock_file_content5 = r"""\documentclass{article}
            \usepackage{xcolor}
            \newcommand{\trig}[3][]{\mathrm{\#2^{\#1}}\left(\#3\right)}
            \newcommand{\trigx}[3][]{\mathrm{\#2}\left({\color{\#1}\#3}\right)}
            \begin{document}
            \[ \trig{sin}{\alpha}, \trig[n]{sin}{\beta},\trig[m]{sin}{\gamma} \]
            \[ \trigx[red]{cos}{2\theta}-\trigx[blue]{sin}{2\theta}=\trigx[green]{cos}{4\theta} \]
            \[ \theta=\trigx[red]{tan^{-1}}{\frac{x}{y}},\trigx[red]{tan}{\alpha+\beta}=\frac{\trigx[blue]{tan}{\alpha}+\trigx[blue]{tan}{\beta}}{1-\trigx[blue]{tan}{\alpha}\trigx[blue]{tan}{\beta}}\]
            \end{document}
            """

    def test_no_macro(self):
        with unittest.mock.patch(
            "builtins.open",
            new=unittest.mock.mock_open(read_data=self.mock_file_content1),
            create=True,
        ) as file_mock:
            result = extract_macro_definitions(file_mock)
            self.assertEqual(result, [])

    def test_no_arguments(self):
        with unittest.mock.patch(
            "builtins.open",
            new=unittest.mock.mock_open(read_data=self.mock_file_content2),
            create=True,
        ) as file_mock:
            result = extract_macro_definitions(file_mock)
            self.assertEqual(
                result,
                [
                    r"\newcommand{\Sin}{\mathrm{sin}\,\theta}",
                    r"\newcommand{\Cos}{\mathrm{cos}\,\theta}",
                    r"\newcommand{\Tan}{\mathrm{tan}\,\theta}",
                ],
            )

    def test_more_than_one_arguments(self):
        with unittest.mock.patch(
            "builtins.open",
            new=unittest.mock.mock_open(read_data=self.mock_file_content4),
            create=True,
        ) as file_mock:
            result = extract_macro_definitions(file_mock)
            self.assertEqual(
                result,
                [
                    r"\newcommand{\trig}[2]{\mathrm{\#1}\left(\#2\right)}",
                    r"\newcommand{\Int}[2]{\int_{\#2}^{\#1}}",
                ],
            )

    def test_optional_arguments(self):
        with unittest.mock.patch(
            "builtins.open",
            new=unittest.mock.mock_open(read_data=self.mock_file_content5),
            create=True,
        ) as file_mock:
            result = extract_macro_definitions(file_mock)
            self.assertEqual(
                result,
                [
                    r"\newcommand{\trig}[3][]{\mathrm{\#2^{\#1}}\left(\#3\right)}",
                    r"\newcommand{\trigx}[3][]{\mathrm{\#2}\left({\color{\#1}\#3}\right)}",
                ],
            )
