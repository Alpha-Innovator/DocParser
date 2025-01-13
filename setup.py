from setuptools import setup, find_packages

setup(
    name="DocParser",
    version="1.0.0",
    description="Process academic papers with .tex source files for layout analysis",
    author="Mao Song",
    author_email="maosong@pjlab.org.cn",
    url="https://github.com/UniModal4Reasoning/DocParser.git",
    license="MIT",
    packages=find_packages(),
    install_requires=[
        "arxiv==1.4.8",
        "graphviz==0.20.1",
        "matplotlib==3.7.1",
        "numpy==1.24.3",
        "pdf2image==1.16.3",
        "pdfminer.six==20221105",
        "Pillow==10.1.0",
        "pyparsing==3.1.1",
        "pytest==7.4.2",
        "scikit_image==0.19.3",
        "setuptools==68.0.0",
        "tqdm==4.66.1",
        "sphinx",
        "arxiv-cleaner",
        "texsoup",
    ],
    python_requires=">=3.8",
    scripts=[],
    entry_points={
        "console_scripts": [
            "vrdu_process=vrdu_data_process.main:main",
        ],
    },
)
