import re


def reduce_empty_lines(latex_file: str) -> None:
    """Reduce multiple empty lines in a LaTeX file.

    This function takes a LaTeX file as input and reduces any sequences
    of multiple blank lines or lines with only whitespace to a single
    empty line. This cleans up formatting in the LaTeX source.

    Arguments:
        latex_file (str): Path to the LaTeX file.

    Returns:
        None

    Remark:
        The file is rewritten in-place with condensed empty lines.
    """
    with open(latex_file) as f:
        latex_content = f.read()
    # Pattern to match multiple empty lines or lines with only whitespace
    pattern = r"\n[\s]+\n"
    latex_content = re.sub(pattern, "\n\n", latex_content)

    with open(latex_file, "w") as f:
        f.write(latex_content)
