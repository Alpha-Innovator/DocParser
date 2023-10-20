import re


def reduce_empty_lines(latex_file):
    with open(latex_file) as f:
        latex_content = f.read()
    # Pattern to match multiple empty lines or lines with only whitespace
    pattern = r"\n[\s]+\n"
    latex_content = re.sub(pattern, "\n\n", latex_content)

    with open(latex_file, "w") as f:
        f.write(latex_content)
