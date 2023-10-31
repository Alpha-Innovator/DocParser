import argparse


def parse_args():
    # Create an argument parser
    parser = argparse.ArgumentParser(
        description='Clean project for submitting on arXiv')

    # Directories
    parser.add_argument('--input', type=str, required=True,
                        help='input directory')
    parser.add_argument('--output', type=str, required=True,
                        help='output directory')
    # Targets
    parser.add_argument('--tex', type=str, required=True,
                        help=('TEX Files to keep (Comma-sepearted paths,' +
                              ' relative to input directory)'))
    # Commands customization
    parser.add_argument('--latex_compiler', default='pdflatex', type=str,
                        help='LaTeX compiler (pdflatex, latex)')
    parser.add_argument('--bib_compiler', default='bibtex', type=str,
                        help='Bibliography compiler (bibtex)')
    parser.add_argument('--latex_extra_args', default='', type=str,
                        help='extra arguments passed to LaTeX compiler')
    parser.add_argument('--bib_extra_args', default='', type=str,
                        help='extra arguments passed to bibliography compiler')
    parser.add_argument('--latexpand_extra_args', default='', type=str,
                        help='extra arguments passed to latexpand')
    # Logging
    parser.add_argument('--verbose', action='store_true',
                        help='turns on verbose logging')

    # Parse the arguments
    args = parser.parse_args()

    # Return the arguments
    return args
