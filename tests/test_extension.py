import unittest
import unittest.mock
from DocParser.vrdu.preprocess import replace_figures_in_tex_files
class TestAbstract(unittest.TestCase):
    def setUp(self) -> None:
        self.initial_content = """
            \\begin{figure}[ht]
            \\centerline{\\includegraphics[width=\\columnwidth]{dir1/time_vs_dimension.pdf}}
            \\subfigure[]{\\includegraphics[width=0.48\\columnwidth]{dir2/iterate_constraint.jpg}} 
            \\subfigure[]{\\epsfig{dir2/iterate_error.eps}} 
            \\subfigure[]{\\psfig[width=0.48\\columnwidth]{time_constraint.es}}
            \\subfigure[]{\\includegraphics[width=0.48\\columnwidth]{dir3/dir4/iterate_correct.png}}
            \\subfigure[]{\\includegraphics[width=0.5\\columnwidth]{dir3/time_error}}
            \\subfigure[]{\\includegraphics[width=0.5\\columnwidth]{dir3/time_error_1}}
            \\label{fig:iteration_information}
        """

        # Simulate image files with correct extensions
        self.image_files = {
            'time_vs_dimension': 'dir1/time_vs_dimension.pdf',
            'iterate_constraint': 'dir2/iterate_constraint.jpg',
            'iterate_error': 'dir2/iterate_error.eps',
            'time_constraint': 'time_constraint.es',
            'iterate_correct': 'dir3/dir4/iterate_correct.png',
            'time_error': 'dir3/time_error.pdf',
            'time_error_1': 'dir3/time_error_1.jpeg'
        }

    def test_replace_figures(self):
        expected_content = """
            \\begin{figure}[ht]
            \\centerline{\\includegraphics[width=\\columnwidth]{dir1/time_vs_dimension.png}}
            \\subfigure[]{\\includegraphics[width=0.48\\columnwidth]{dir2/iterate_constraint.jpg}} 
            \\subfigure[]{\\includegraphics{dir2/iterate_error.png}} 
            \\subfigure[]{\\includegraphics[width=0.48\\columnwidth]{time_constraint.png}}
            \\subfigure[]{\\includegraphics[width=0.48\\columnwidth]{dir3/dir4/iterate_correct.png}}
            \\subfigure[]{\\includegraphics[width=0.5\\columnwidth]{dir3/time_error.png}}
            \\subfigure[]{\\includegraphics[width=0.5\\columnwidth]{dir3/time_error_1.jpeg}}
            \\label{fig:iteration_information}
        """

        with unittest.mock.patch(
            "builtins.open",
            new=unittest.mock.mock_open(read_data=self.initial_content),
            create=True,
        ) as file_mock:
            replace_figures_in_tex_files(file_mock,self.image_files)
            file_mock.assert_called_with(file_mock, "w")
            file_mock().write.assert_called_with(
                expected_content
            )