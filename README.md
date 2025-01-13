# DocParser

A tool for processing academic papers with `.tex` source files to extract:

1. Object detection results
2. LaTeX source code with visual bounding box pairs
3. Layout reading orders

## Project Links

- GitHub Repository: <https://github.com/Alpha-Innovator/DocGenome>
- HuggingFace dataset: <https://huggingface.co/datasets/U4R/DocGenome/tree/main>

## Installation

### Prerequisites

1. **Python Environment**
   - Python 3.8 or higher
   - Anaconda (recommended) - [Installation Guide](https://docs.anaconda.com/free/anaconda/install/index.html)

2. **TeX Live Distribution**
   - Required for LaTeX compilation
   - Installation guide available at [tug.org/texlive](https://www.tug.org/texlive/)

   For Ubuntu users:

   ```bash
   sudo apt-get install texlive-full  # Requires ~5.4GB disk space
   ```

   Note: `texlive-full` is recommended to avoid missing package errors. See [package differences](https://tex.stackexchange.com/a/504566).

### Setup

1. Create and activate conda environment:

   ```bash
   conda create --name doc_parser python=3.8
   conda activate doc_parser
   ```

2. Install the package:

   ```bash
   pip install -e .
   ```

## Usage

Run the parser on your LaTeX file:

```bash
python main.py --file_name path_to_paper/paper.tex
```

### Output Structure

Results are stored in `path_to_paper/output/result`:

```
path_to_paper
├── output
│   ├── paper_colored/           # Rendered paper images
│   │   ├── thread-0001-page-01.jpg
│   │   └── ...
│   └── result/
│       ├── layout_annotation.json    # Object detection results (COCO format)
│       ├── reading_annotation.json   # Bounding box to LaTeX source mapping
│       ├── ordering_annotation.json  # Reading order relationships
│       ├── quality_report.json      
│       ├── texts.json               # Original tex contents
│       ├── layout_info.json         # Raw detection results
│       ├── layout_metadata.json     # Paper layout information
│       ├── page_*.jpg              # Pages with bounding boxes
│       └── block_*.jpg             # Individual block images
```

### Output Components

1. **Object Detection Results**
   - `layout_annotation.json` and `page_*.jpg`
   - Uses [COCO format](https://cocodataset.org/#format-data)

2. **Reading Detection Results**
   - `reading_annotation.json`
   - Maps bounding boxes to original LaTeX content

3. **Reading Order Results**
   - `ordering_annotation.json`
   - Defines relationships between blocks using triples: (relationship, from, to)

## Categories

Each bounding box is classified into one of these categories:

| Category | Name | Super Category | Description |
|----------|------|----------------|-------------|
| 0 | Algorithm | Algorithm | Algorithm environments |
| 1 | Caption | Caption | Figure, Table, Algorithm captions |
| 2 | Equation | Equation | Display equations (equation, align) |
| 3 | Figure | Figure | Figures |
| 4 | Footnote | Footnote | Footnotes |
| 5 | List | List | itemize, enumerate, description |
| 6 | Others | Others | Currently unused |
| 7 | Table | Table | Tables |
| 8 | Text | Text | Plain text without equations |
| 9 | Text-EQ | Text | Text with inline equations |
| 10 | Title | Title | Section/subsection titles |
| 11 | Reference | Reference | References |
| 12 | PaperTitle | Title | Paper title |
| 13 | Code | Algorithm | Code listings |
| 14 | Abstract | Text | Paper abstract |

## Troubleshooting

### Common Issues

1. **Latexpand Error**

   ```bash
   ValueError: Failed to run the command "latexpand..."
   ```

   Solution:
   - Check latexpand version: `latexpand --help`
   - If < 1.6, upgrade using:
     1. Download from [latexpand v1.6](https://gitlab.com/latexpand/latexpand/-/tags/v1.6)
     2. Update existing script: `sudo vim $(which latexpand)`

2. **PDF2Image Error**

   ```bash
   PDFInfoNotInstalledError: Unable to get page count
   ```

   Solution:

   ```bash
   sudo apt-get install poppler-utils
   ```

3. **Missing Block PDF**
   - If `block_*.pdf` is missing, the LaTeX rendering likely failed
   - This is case-specific and requires manual investigation

## Known Limitations

1. **Custom Environments**: Some custom environments (e.g., `\newtheorem{defn}[thm]{Definition}`) require manual addition to `envs.text_envs`
2. **Rendering Issues**: Some environments may fail during PDF compilation
3. **Special Figures**: TikZ and similar formats may not be correctly classified

## Documentation

Build the documentation using Sphinx:

```bash
cd docs
sphinx-build . _build
```

View the documentation by opening `docs/_build/index.html` in a browser.

## Acknowledgements

Built using:

- [Texsoup](https://texsoup.alvinwan.com/)
- [pdf2image](https://pypi.org/project/pdf2image/)
- [pdfminer.six](https://pdfminersix.readthedocs.io/en/latest/index.html)
- [arxiv_cleaner](https://github.com/elsa-lab/arxiv-cleaner.git)

# Citation

if you found this package useful, please cite:

```bibtex
@article{xia2024docgenome,
  title={DocGenome: An Open Large-scale Scientific Document Benchmark for Training and Testing Multi-modal Large Language Models},
  author={Xia, Renqiu and Mao, Song and Yan, Xiangchao and Zhou, Hongbin and Zhang, Bo and Peng, Haoyang and Pi, Jiahao and Fu, Daocheng and Wu, Wenjie and Ye, Hancheng and others},
  journal={arXiv preprint arXiv:2406.11633},
  year={2024}
}
```
