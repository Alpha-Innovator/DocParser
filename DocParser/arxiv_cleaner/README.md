# arXiv Cleaner

Clean LaTeX project for submitting to arXiv.

## Features

* Produce only the files needed for the TEX files you choose
* Expand all the files which are included by `\input` or `\include` directives
* Remove all comments from the code (which are visible on arXiv because the uploaded LaTeX project is downloadable)
* Remove unnecessary blank lines
* Support UTF-8 encoding files

See the difference between `example_elsa/` and `example_elsa_cleaned/`.

## Prerequisites

1. Linux-based terminals (For Windows, I recommend using [git-sdk](https://github.com/git-for-windows/build-extra/releases))
2. Python 3.5 or higher
3. LaTeX programs (Can be installed altogether by [TeX Live](https://www.tug.org/texlive/))
    1. pdflatex
    2. bibtex
    3. [latexpand](https://www.ctan.org/pkg/latexpand) 1.5

## Usage

1. Clone this Git project to your computer
2. Open a terminal window to the Git project directory
3. Run the main program `arxiv_cleaner.main` with arguments described as follows

Specify the input directory containing the LaTeX project, the output directory and the TEX files you want to keep (relative paths in the input directory)

```bash
python -m arxiv_cleaner.main --input=<Input directory> --output=<Output directory> --tex=<TEX files to keep>
```

Text files (`.tex`, `.cls`, `.clo`, `.sty`, `.bst`) required by the TEX files to keep will be cleaned and copied to the output directory. Other files (e.g., images) required by the TEX files to keep will be copied to the output directory.

## Examples

Try cleaning the example project as follows

```bash
python -m arxiv_cleaner.main --input=example_elsa --output=example_elsa_cleaned --tex=main.tex,sup.tex
```

See other directories (`example_aaai`, `example_ieee`, ...) for more examples.

## References

* [google-research/arxiv-latex-cleaner - GitHub](https://github.com/google-research/arxiv-latex-cleaner)
* [Package latexpand - CTAN](https://www.ctan.org/pkg/latexpand)

## Resources

* [Considerations for TeX Submissions | arXiv e-print repository](https://arxiv.org/help/submit_tex)
