from setuptools import setup, find_packages

setup(
    name="vrdu_data_process",
    version="0.5.0",
    description="process the academic papers with .tex source files",
    author="Mao Song",
    author_email="maosong@pjlab.org.cn",
    url="https://github.com/MaoSong2022/vrdu_data_process",
    license="MIT",
    packages=find_packages(),
    install_requires=[
        "arxiv==1.4.8",
        "graphviz==0.20.1",
        "matplotlib==3.7.1",
        "numpy==1.24.3",
        "pdf2image==1.16.3",
        "pdfminer.six==20221105",
        "Pillow==9.4.0",
        "Pillow==10.1.0",
        "pyparsing==3.1.1",
        "pytest==7.4.2",
        "scikit_image==0.19.3",
        "setuptools==68.0.0",
        "tqdm=4.66.1",
    ],
    scripts=[
        "vrdu/compile_latex.sh",
    ],
    entry_points={
        "console_scripts": [],
    },
)
