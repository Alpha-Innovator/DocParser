import unittest
import unittest.mock


from DocParser.vrdu.renderer import Renderer


class TestAbstract(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_file_content1 = (
            """\\documentclass{article}\\begin{document}\\end{document}"""
        )

        self.mock_file_content2 = """\\documentclass{article}\\begin{document}\\begin{abstract}\n   This is the content of abstract.\n \\end{abstract}\\end{document}"""
        self.mock_file_content3 = "\\begin{abstract}\nWe consider the projection onto the $\\ell_{1, \\infty}$ norm ball for solving group sparse optimization problems arising in multi-task learning. \nBased on the primal-dual gradient method (PDG), we present a novel primal-dual Newton method, which updates the primal and dual iterates incrementally with Newton steps. \nWe exploit the problem-inherent structure so that the closed-form for the primal-dual Newton steps can be derived easily. \nCompared with existing algorithms, our approach does not need to maintain the primal feasibility, nor require the computation of the $\\ell_1$ ball projection subproblems. \nWe prove that our algorithm terminates after a finite number of iterations. \nNumerical simulations on synthetic and real-world data show that our proposed method is faster than the previous state-of-the-art.\n\n\\end{abstract}"
        self.renderer = Renderer()

    def test_no_abstract(self):
        with unittest.mock.patch(
            "builtins.open",
            new=unittest.mock.mock_open(read_data=self.mock_file_content1),
            create=True,
        ) as file_mock:
            self.renderer.render_abstract(file_mock)
            file_mock.assert_called_with(file_mock)

    def test_one_abstract1(self):
        with unittest.mock.patch(
            "builtins.open",
            new=unittest.mock.mock_open(read_data=self.mock_file_content2),
            create=True,
        ) as file_mock:
            self.renderer.render_abstract(file_mock)
            file_mock.assert_called_with(file_mock, "w")
            file_mock().write.assert_called_with(
                """\\documentclass{article}\\begin{document}{\\begin{abstract}\\color{Abstract_color}\n   This is the content of abstract.\n \\end{abstract}}\\end{document}"""
            )

    def test_one_abstract2(self):
        with unittest.mock.patch(
            "builtins.open",
            new=unittest.mock.mock_open(read_data=self.mock_file_content3),
            create=True,
        ) as file_mock:
            self.renderer.render_abstract(file_mock)
            file_mock.assert_called_with(file_mock, "w")
            file_mock().write.assert_called_with(
                "{\\begin{abstract}\\color{Abstract_color}\nWe consider the projection onto the $\\ell_{1, \\infty}$ norm ball for solving group sparse optimization problems arising in multi-task learning. \nBased on the primal-dual gradient method (PDG), we present a novel primal-dual Newton method, which updates the primal and dual iterates incrementally with Newton steps. \nWe exploit the problem-inherent structure so that the closed-form for the primal-dual Newton steps can be derived easily. \nCompared with existing algorithms, our approach does not need to maintain the primal feasibility, nor require the computation of the $\\ell_1$ ball projection subproblems. \nWe prove that our algorithm terminates after a finite number of iterations. \nNumerical simulations on synthetic and real-world data show that our proposed method is faster than the previous state-of-the-art.\n\n\\end{abstract}}"
            )
