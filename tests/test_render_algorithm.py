import unittest
import unittest.mock


from DocParser.vrdu.renderer import Renderer


class TestAlgorithm(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_file_content1 = (
            """\\documentclass{article}\\begin{document}\\end{document}"""
        )
        self.mock_file_content2 = """\\documentclass{article}\\begin{document}\\begin{algorithm}[!htb]\n    \\caption{Primal-dual Newton Method}\n    \\label{alg:PDN}\n    \\begin{algorithmic}[1]\n        \\STATE Input: $\\mathbf{A}\\in\\mathbb{R}_+^{m\\times n}$, $C>0$.\n        \\IF{$\\|\\mathbf{A}\\|_{1,\\infty}\\leq C$}\n            \\STATE \\textbf{return} $\\mathbf{A}$\n        \\ENDIF\n        \\STATE \\textbf{Initialize} $\\lambda^0=(\\sum_{i=1}^{m}\\|\\bm{a}_i\\|_\\infty-C)/m$, $\\boldsymbol\\mu^0=\\mathbf{0}_{m\\times 1}$ and $\\beta_i^0=1/|\\mathcal{I}(\\mu_i^0)|$ for $i\\in[m]$.\n\n        \\FOR{$k=0,1,2,\\dots$}\n        \\STATE Update $\\mathcal{B}^k=\\{i|\\|\\bm{a}_i\\|_1>\\lambda^k\\}$.\n\\STATE Update $\\mu_i^k$ \n        \\begin{equation}\\label{eq:alg_update_mu}\n            \\mu_i^{k+1} =\\begin{cases}\n                \\mu_i^k-\\beta_i^k\\nabla_i\\mathcal{L}\\left(\\boldsymbol\\mu^k,\\lambda^k\\right), &\\text{ if }i\\in\\mathcal{B}^k\\\\\n                0, &\\text{ otherwise }\n            \\end{cases}\n        \\end{equation}\n        \\STATE Compute $\\beta_i^{k+1}=1/|\\mathcal{I}(\\mu_i^{k+1})|$ for $i\\in\\mathcal{B}^k$.\n        \\STATE Update $\\lambda^k$\n            \\begin{equation}\\label{eq:alg_update_lambda}\n                \\lambda^{k+1} = \\lambda^k + \\frac{\\left[\\sum_{i\\in\\mathcal{B}^k}\\mu_i^{k+1}-C\\right]_+}{\\sum_{i\\in\\mathcal{B}^k}\\beta_i^{k+1}}.\n            \\end{equation}\n        \\IF{$|\\sum_{i\\in\\mathcal{B}^k}\\mu_i^{k+1}-C|\\leq0$}\n\\STATE \\textbf{Break}\n        \\ENDIF\n\n        \\ENDFOR\n        \\STATE \\textbf{return} $\\mathbf{W}^*=\\min(\\mathbf{A},\\boldsymbol\\mu^k\\bm{1}_{1\\times n})$. \n    \\end{algorithmic}\n\\end{algorithm}\\end{document}"""
        self.renderer = Renderer()

    def test_no_algorithm(self):
        with unittest.mock.patch(
            "builtins.open",
            new=unittest.mock.mock_open(read_data=self.mock_file_content1),
            create=True,
        ) as file_mock:
            self.renderer.render_algorithm(file_mock)
            file_mock.assert_called_with(file_mock, "w")
            file_mock().write.assert_called_with(
                """\\documentclass{article}\\begin{document}\\end{document}"""
            )

    def test_one_algorithm(self):
        with unittest.mock.patch(
            "builtins.open",
            new=unittest.mock.mock_open(read_data=self.mock_file_content2),
            create=True,
        ) as file_mock:
            self.renderer.render_algorithm(file_mock)
            file_mock.assert_called_with(file_mock, "w")
            file_mock().write.assert_called_with(
                """\\documentclass{article}\\begin{document}\\begin{algorithm}[!htb]\n    {\\color{Algorithm_color}\\caption{Primal-dual Newton Method}\n    \\label{alg:PDN}\n    \\begin{algorithmic}[1]\n        \\STATE Input: $\\mathbf{A}\\in\\mathbb{R}_+^{m\\times n}$, $C>0$.\n        \\IF{$\\|\\mathbf{A}\\|_{1,\\infty}\\leq C$}\n            \\STATE \\textbf{return} $\\mathbf{A}$\n        \\ENDIF\n        \\STATE \\textbf{Initialize} $\\lambda^0=(\\sum_{i=1}^{m}\\|\\bm{a}_i\\|_\\infty-C)/m$, $\\boldsymbol\\mu^0=\\mathbf{0}_{m\\times 1}$ and $\\beta_i^0=1/|\\mathcal{I}(\\mu_i^0)|$ for $i\\in[m]$.\n\n        \\FOR{$k=0,1,2,\\dots$}\n        \\STATE Update $\\mathcal{B}^k=\\{i|\\|\\bm{a}_i\\|_1>\\lambda^k\\}$.\n\\STATE Update $\\mu_i^k$ \n        \\begin{equation}\\label{eq:alg_update_mu}\n            \\mu_i^{k+1} =\\begin{cases}\n                \\mu_i^k-\\beta_i^k\\nabla_i\\mathcal{L}\\left(\\boldsymbol\\mu^k,\\lambda^k\\right), &\\text{ if }i\\in\\mathcal{B}^k\\\\\n                0, &\\text{ otherwise }\n            \\end{cases}\n        \\end{equation}\n        \\STATE Compute $\\beta_i^{k+1}=1/|\\mathcal{I}(\\mu_i^{k+1})|$ for $i\\in\\mathcal{B}^k$.\n        \\STATE Update $\\lambda^k$\n            \\begin{equation}\\label{eq:alg_update_lambda}\n                \\lambda^{k+1} = \\lambda^k + \\frac{\\left[\\sum_{i\\in\\mathcal{B}^k}\\mu_i^{k+1}-C\\right]_+}{\\sum_{i\\in\\mathcal{B}^k}\\beta_i^{k+1}}.\n            \\end{equation}\n        \\IF{$|\\sum_{i\\in\\mathcal{B}^k}\\mu_i^{k+1}-C|\\leq0$}\n\\STATE \\textbf{Break}\n        \\ENDIF\n\n        \\ENDFOR\n        \\STATE \\textbf{return} $\\mathbf{W}^*=\\min(\\mathbf{A},\\boldsymbol\\mu^k\\bm{1}_{1\\times n})$. \n    \\end{algorithmic}\n}\\end{algorithm}\\end{document}"""
            )
