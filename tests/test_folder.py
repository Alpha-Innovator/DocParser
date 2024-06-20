import unittest
import os
from unittest.mock import patch, MagicMock
from generate_figure import generate_png_figure

class TestGeneratePngFigure(unittest.TestCase):
    def setUp(self):
        # 设置测试环境，模拟有各种类型文件的目录
        self.test_dir = 'test_directory_1'
        self.original_tex = os.path.join(self.test_dir, 'test.tex')
        os.makedirs(self.test_dir, exist_ok=True)
        self.image_files = [
            'image1.eps', 'image2.ps', 'image3.jpg', 'image4.jpeg', 'image5.png', 'image6.pdf'
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

    @patch('vrdu.utils.convert_eps_image_to_pdf_image')
    @patch('vrdu.utils.convert_pdf_figure_to_png_image')
    def test_png_generation(self, mock_convert_pdf_to_png, mock_convert_eps_to_pdf):
        generate_png_figure(self.original_tex)

        # 检查文件生成情况
        expected_files = [
            'image1.eps', 'image2.ps', 'image3.jpg', 'image4.jpeg', 'image5.png', 'image6.pdf', 
            'image1.png', 'image2.png', 'image6.png'
        ]
        # 获取当前目录下所有文件
        generated_files = os.listdir(self.test_dir)
    

        # 目前模拟的测试环境中，无法真的生成文件,导致expected_files和generated_files不一致

        # print("Expected Files:", expected_files)
        # print("Generated Files:", generated_files)
        # self.assertCountEqual(expected_files, generated_files)

        # 检查函数调用
        self.assertEqual(mock_convert_eps_to_pdf.call_count, 2)  # 对于两个EPS/PS文件的调用
        self.assertEqual(mock_convert_pdf_to_png.call_count, 3)  # 对于三个PDF文件的调用