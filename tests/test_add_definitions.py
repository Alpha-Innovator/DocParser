import unittest
import unittest.mock

from DocParser.vrdu.renderer import Renderer


def test_add_color_definition1():
    mock_file_content = """\\documentclass{article}\\begin{document}\\end{document}"""
    with unittest.mock.patch(
        "builtins.open",
        new=unittest.mock.mock_open(read_data=mock_file_content),
        create=True,
    ) as file_mock:
        renderer = Renderer()
        renderer.add_color_definition(file_mock)
        file_mock.assert_called_with(file_mock, "w")
        file_mock().write.assert_called_with(
            """\\documentclass{article}\n\\usepackage{xcolor}\n\\definecolor{Algorithm_color}{RGB}{0, 0, 0}\n\\definecolor{Caption_color}{RGB}{0, 0, 0}\n\\definecolor{Equation_color}{RGB}{0, 0, 0}\n\\definecolor{Figure_color}{RGB}{0, 0, 0}\n\\definecolor{Footnote_color}{RGB}{0, 0, 0}\n\\definecolor{List_color}{RGB}{0, 0, 0}\n\\definecolor{Others_color}{RGB}{0, 0, 0}\n\\definecolor{Table_color}{RGB}{0, 0, 0}\n\\definecolor{Text_color}{RGB}{0, 0, 0}\n\\definecolor{Text-EQ_color}{RGB}{0, 0, 0}\n\\definecolor{Title_color}{RGB}{0, 0, 0}\n\\definecolor{Reference_color}{RGB}{0, 0, 0}\n\\definecolor{PaperTitle_color}{RGB}{0, 0, 0}\n\\definecolor{Code_color}{RGB}{0, 0, 0}\n\\definecolor{Abstract_color}{RGB}{0, 0, 0}\n\\begin{document}\\end{document}"""
        )


def test_add_color_definition2():
    mock_file_content = """\\documentclass{article}\n\\usepackage[usenames,dvipsnames]{color}\\begin{document}\\end{document}"""
    with unittest.mock.patch(
        "builtins.open",
        new=unittest.mock.mock_open(read_data=mock_file_content),
        create=True,
    ) as file_mock:
        renderer = Renderer()
        renderer.add_color_definition(file_mock)
        file_mock.assert_called_with(file_mock, "w")
        file_mock().write.assert_called_with(
            """\\documentclass{article}\n\\usepackage[usenames,dvipsnames]{color}\n\\usepackage{xcolor}\n\\definecolor{Algorithm_color}{RGB}{0, 0, 0}\n\\definecolor{Caption_color}{RGB}{0, 0, 0}\n\\definecolor{Equation_color}{RGB}{0, 0, 0}\n\\definecolor{Figure_color}{RGB}{0, 0, 0}\n\\definecolor{Footnote_color}{RGB}{0, 0, 0}\n\\definecolor{List_color}{RGB}{0, 0, 0}\n\\definecolor{Others_color}{RGB}{0, 0, 0}\n\\definecolor{Table_color}{RGB}{0, 0, 0}\n\\definecolor{Text_color}{RGB}{0, 0, 0}\n\\definecolor{Text-EQ_color}{RGB}{0, 0, 0}\n\\definecolor{Title_color}{RGB}{0, 0, 0}\n\\definecolor{Reference_color}{RGB}{0, 0, 0}\n\\definecolor{PaperTitle_color}{RGB}{0, 0, 0}\n\\definecolor{Code_color}{RGB}{0, 0, 0}\n\\definecolor{Abstract_color}{RGB}{0, 0, 0}\n\\begin{document}\\end{document}"""
        )


def test_add_layout_definition():
    pass
    mock_file_content = """\\documentclass{article}\\begin{document}\\end{document}"""
    with unittest.mock.patch(
        "builtins.open",
        new=unittest.mock.mock_open(read_data=mock_file_content),
        create=True,
    ) as file_mock:
        renderer = Renderer()
        renderer.add_layout_definition(file_mock)
        file_mock.assert_called_with(file_mock, "w")
        file_mock().write.assert_called_with(
            """\\documentclass{article}\\begin{document}\n\\message{[vrdu_data_process: Info]}\n\\message{[vrdu_data_process: The columnwidth is: \\the\\columnwidth]}\n\\message{[vrdu_data_process: The columnsep is: \\the\\columnsep]}\n\\message{[vrdu_data_process: The textwidth is: \\the\\textwidth]}\n\\message{[vrdu_data_process: The paperwidth is: \\the\\paperwidth]}\n\\message{[vrdu_data_process: The hoffset is: \\the\\hoffset]}\n\\message{[vrdu_data_process: The voffset is: \\the\\voffset]}\n\\message{[vrdu_data_process: The oddsidemargin is: \\the\\oddsidemargin]}\n\\message{[vrdu_data_process: The evensidemargin is: \\the\\evensidemargin]}\n\\message{[vrdu_data_process: The marginparwidth is: \\the\\marginparwidth]}\n\\message{[vrdu_data_process: The marginparsep is: \\the\\marginparsep]}\n\\message{[vrdu_data_process: The topmargin is: \\the\\topmargin]}\n\\message{[vrdu_data_process: The headheight is: \\the\\headheight]}\n\\message{[vrdu_data_process: The headsep is: \\the\\headsep]}\n\\message{[vrdu_data_process: The footskip is: \\the\\footskip]}\n\\message{[vrdu_data_process: The textheight is: \\the\\textheight]}\n\\end{document}"""
        )
