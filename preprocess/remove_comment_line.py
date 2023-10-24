import re


def remove_comment_line(latex_file: str):
    """Remove comment lines from a LaTeX file.

    This function takes a LaTeX file as input and removes any comment
    lines starting with '%'. LaTeX comments are identified using a
    regular expression.

    The file contents are read, comments are removed via regex
    substitution, and the modified content is written back to
    overwrite the original file.

    Arguments:
        latex_file (str): Path to the LaTeX input file.

    Returns:
        None

    Remark:
        The input file is rewritten in-place without comment lines.
    """
    # Regular expression pattern to match LaTeX comments
    comment_pattern = r"(?<!\\)%.*?$"

    # Read the LaTeX file
    with open(latex_file, "r") as file:
        content = file.read()

    # Remove comments using regular expression substitution
    content = re.sub(comment_pattern, "", content, flags=re.MULTILINE)

    # Write the modified content back to the LaTeX file
    with open(latex_file, "w") as file:
        file.write(content)
