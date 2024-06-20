import unittest
import os
import unittest.mock


from replace_figure_extension import replace_figures_extension_with_png


class TestAbstract(unittest.TestCase):
    def setUp(self) -> None:
        
        # 测试环境的设置，包括创建测试文件夹和文件
        self.test_dir = 'test_directory'
        self.original_tex = os.path.join(self.test_dir, 'test.tex')
        os.makedirs(self.test_dir, exist_ok=True)
        with open(self.original_tex, 'w') as f:
            f.write(r'''
                    \\begin{figure}[ht]
                    \\centerline{\\includegraphics[width=\\columnwidth]{figures/time_vs_dimension.pdf}}
                    \\subfigure[]{\\includegraphics[width=0.48\\columnwidth]{figures/iterate_constraint.jpg}} 
                    \\subfigure[]{\\epsfig{figures/iterate_error.eps}} 
                    \\subfigure[]{\\psfig[width=0.48\\columnwidth]{figures/time_constraint.ps}}
                    \\subfigure[]{\\includegraphics[width=0.48\\columnwidth]{figures/iterate_correct.png}}
                    \\subfigure[]{\\includegraphics[width=0.5\\columnwidth]{figures/time_error}}
                    \\subfigure[]{\\includegraphics[width=0.5\\columnwidth]{figures/time_error_1}}
                    \\label{fig:iteration_information}
                    ''')

        # 模拟图片文件
        self.image_files = [
            'time_vs_dimension.pdf', 'iterate_constraint.jpg', 'iterate_error.eps', 'time_constraint.ps', 'iterate_correct.png', 'time_error.pdf', 'time_error_1.jpeg'
        ]
        for file_name in self.image_files:
            with open(os.path.join(self.test_dir, file_name), 'w') as f:
                f.write('dummy content')

    def tearDown(self):
        # 清理测试创建的文件和目录
        for root, dirs, files in os.walk(self.test_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(self.test_dir)

    def test(self):
        replace_figures_extension_with_png(self.original_tex)
        with open(self.original_tex, 'r') as f:
            content = f.read()
        self.assertEqual(content, r'''
                    \\begin{figure}[ht]
                    \\centerline{\\includegraphics[width=\\columnwidth]{figures/time_vs_dimension.png}}
                    \\subfigure[]{\\includegraphics[width=0.48\\columnwidth]{figures/iterate_constraint.jpg}} 
                    \\subfigure[]{\\includegraphics{figures/iterate_error.png}} 
                    \\subfigure[]{\\includegraphics[width=0.48\\columnwidth]{figures/time_constraint.png}}
                    \\subfigure[]{\\includegraphics[width=0.48\\columnwidth]{figures/iterate_correct.png}}
                    \\subfigure[]{\\includegraphics[width=0.5\\columnwidth]{figures/time_error.png}}
                    \\subfigure[]{\\includegraphics[width=0.5\\columnwidth]{figures/time_error_1.jpeg}}
                    \\label{fig:iteration_information}
                    ''')
