import unittest
import unittest.mock


from DocParser.vrdu.renderer import Renderer


class TestCode(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_file_content1 = (
            """\\documentclass{article}\\begin{document}\\end{document}"""
        )
        self.mock_file_content2 = r"""\documentclass{article}\n        \begin{document}\n        \begin{verbatim}\n        Text enclosed inside \texttt{verbatim} environment \n        is printed directly \n        and all \LaTeX{} commands are ignored.\n        \end{verbatim}\n        \end{document}"""
        self.mock_file_content3 = r"""\n\documentclass{article}\n\begin{document}\n\begin{verbatim*}\nText enclosed inside \texttt{verbatim} environment \nis printed directly \nand all \LaTeX{} commands are ignored.\n\end{verbatim*}\n\end{document}"""
        self.mock_file_content4 = r"""\documentclass{article}\begin{document}\lstinputlisting[language=Octave, firstline=2, lastline=12]{BitXorMatrix.m}\end{document}"""
        self.mock_file_content5 = r"""\documentclass{article}\n\usepackage{listings}\n\usepackage{xcolor}\n\n\definecolor{codegreen}{rgb}{0,0.6,0}\n\definecolor{codegray}{rgb}{0.5,0.5,0.5}\n\definecolor{codepurple}{rgb}{0.58,0,0.82}\n\definecolor{backcolour}{rgb}{0.95,0.95,0.92}\n\n\lstdefinestyle{mystyle}{\n    backgroundcolor=\color{backcolour},   \n    commentstyle=\color{codegreen},\n    keywordstyle=\color{magenta},\n    numberstyle=\tiny\color{codegray},\n    stringstyle=\color{codepurple},\n    basicstyle=\ttfamily\footnotesize,\n    breakatwhitespace=false,         \n    breaklines=true,                 \n    captionpos=b,                    \n    keepspaces=true,                 \n    numbers=left,                    \n    numbersep=5pt,                  \n    showspaces=false,                \n    showstringspaces=false,\n    showtabs=false,                  \n    tabsize=2\n}\n\n\lstset{style=mystyle}\n\n\begin{document}\nThe next code will be directly imported from a file\n\n\lstinputlisting[language=Octave]{BitXorMatrix.m}\n\end{document}"""
        self.mock_file_content6 = r"""\documentclass{article}\n\usepackage{program}   \n\begin{document}\n\begin{program}\n\IF x = 1 \AR y:=y+1\n\BAR x = 2 \AR y:=y^2\n\utdots\n\BAR x = n \AR y:=\displaystyle\sum_{i=1}^n y_i \FI\n\n\DO 2 \origbar x \AND x>0 \AR x:= x/2\n\BAR \NOT 2 \origbar x \AR x:= \modbar{x+3} \OD\n\end{program}\n\end{document}"""
        self.renderer = Renderer()

    def test_no_code(self):
        with unittest.mock.patch(
            "builtins.open",
            new=unittest.mock.mock_open(read_data=self.mock_file_content1),
            create=True,
        ) as file_mock:
            self.renderer.render_code(file_mock)
            file_mock.assert_called_with(file_mock, "w")
            file_mock().write.assert_called_with(
                """\\documentclass{article}\\begin{document}\\end{document}"""
            )

    def test_one_code1(self):
        with unittest.mock.patch(
            "builtins.open",
            new=unittest.mock.mock_open(read_data=self.mock_file_content2),
            create=True,
        ) as file_mock:
            self.renderer.render_code(file_mock)
            file_mock.assert_called_with(file_mock, "w")
            file_mock().write.assert_called_with(
                r"""\documentclass{article}\n        \begin{document}\n        {\color{Code_color}\begin{verbatim}\n        Text enclosed inside \texttt{verbatim} environment \n        is printed directly \n        and all \LaTeX{} commands are ignored.\n        \end{verbatim}}\n        \end{document}"""
            )

    def test_one_code2(self):
        with unittest.mock.patch(
            "builtins.open",
            new=unittest.mock.mock_open(read_data=self.mock_file_content3),
            create=True,
        ) as file_mock:
            self.renderer.render_code(file_mock)
            file_mock.assert_called_with(file_mock, "w")
            file_mock().write.assert_called_with(
                r"""\n\documentclass{article}\n\begin{document}\n{\color{Code_color}\begin{verbatim*}\nText enclosed inside \texttt{verbatim} environment \nis printed directly \nand all \LaTeX{} commands are ignored.\n\end{verbatim*}}\n\end{document}"""
            )

    def test_one_code3(self):
        with unittest.mock.patch(
            "builtins.open",
            new=unittest.mock.mock_open(read_data=self.mock_file_content4),
            create=True,
        ) as file_mock:
            self.renderer.render_code(file_mock)
            file_mock.assert_called_with(file_mock, "w")
            file_mock().write.assert_called_with(
                r"""\documentclass{article}\begin{document}{\color{Code_color}\lstinputlisting[language=Octave, firstline=2, lastline=12]{BitXorMatrix.m}}\end{document}"""
            )

    def test_no_lstset(self):
        with unittest.mock.patch(
            "builtins.open",
            new=unittest.mock.mock_open(read_data=self.mock_file_content1),
            create=True,
        ) as file_mock:
            self.renderer.remove_predefined_color(file_mock)
            file_mock.assert_called_with(file_mock, "w")
            file_mock().write.assert_called_with(
                """\\documentclass{article}\\begin{document}\\end{document}"""
            )

    def test_remove_lstset(self):
        with unittest.mock.patch(
            "builtins.open",
            new=unittest.mock.mock_open(read_data=self.mock_file_content5),
            create=True,
        ) as file_mock:
            self.renderer.remove_predefined_color(file_mock)
            file_mock.assert_called_with(file_mock, "w")
            file_mock().write.assert_called_with(
                r"""\documentclass{article}\n\usepackage{listings}\n\usepackage{xcolor}\n\n\definecolor{codegreen}{rgb}{0,0.6,0}\n\definecolor{codegray}{rgb}{0.5,0.5,0.5}\n\definecolor{codepurple}{rgb}{0.58,0,0.82}\n\definecolor{backcolour}{rgb}{0.95,0.95,0.92}\n\n\lstdefinestyle{mystyle}{\n    backgroundcolor=\color{backcolour},   \n    commentstyle=\color{codegreen},\n    keywordstyle=\color{magenta},\n    numberstyle=\tiny\color{codegray},\n    stringstyle=\color{codepurple},\n    basicstyle=\ttfamily\footnotesize,\n    breakatwhitespace=false,         \n    breaklines=true,                 \n    captionpos=b,                    \n    keepspaces=true,                 \n    numbers=left,                    \n    numbersep=5pt,                  \n    showspaces=false,                \n    showstringspaces=false,\n    showtabs=false,                  \n    tabsize=2\n}\n\n\n\n\begin{document}\nThe next code will be directly imported from a file\n\n\lstinputlisting[language=Octave]{BitXorMatrix.m}\n\end{document}"""
            )

    def test_one_program(self):
        with unittest.mock.patch(
            "builtins.open",
            new=unittest.mock.mock_open(read_data=self.mock_file_content6),
            create=True,
        ) as file_mock:
            self.renderer.render_code(file_mock)
            file_mock.assert_called_with(file_mock, "w")
            file_mock().write.assert_called_with(
                r"""\documentclass{article}\n\usepackage{program}   \n\begin{document}\n{\color{Code_color}\begin{program}\n\IF x = 1 \AR y:=y+1\n\BAR x = 2 \AR y:=y^2\n\utdots\n\BAR x = n \AR y:=\displaystyle\sum_{i=1}^n y_i \FI\n\n\DO 2 \origbar x \AND x>0 \AR x:= x/2\n\BAR \NOT 2 \origbar x \AR x:= \modbar{x+3} \OD\n\end{program}}\n\end{document}"""
            )
