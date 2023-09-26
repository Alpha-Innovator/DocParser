import os

from TexSoup.TexSoup import TexSoup


def resolve_recursively(tex: str, file_path: str) -> TexSoup:
    """
    Recursively resolves subimports, imports, includes, and inputs in a TeX document.

    Args:
        tex (str): The TeX document as a string.
        file_path (str): The file path of the TeX document.

    Returns:
        TexSoup: A TexSoup object representing the resolved TeX document.

    """
    # soupify
    soup = TexSoup(tex)
    directory = os.path.dirname(file_path)

    # resolve subimports
    for subimport in soup.find_all("subimport"):
        path = subimport.args[0] + subimport.args[1]
        subimport.replace_with(
            *resolve_recursively(open(path).read().strip(), file_path).contents
        )

    # resolve imports
    for _import in soup.find_all("import"):
        _import.replace_with(
            *resolve_recursively(
                open(_import.args[0]).read().strip(), file_path
            ).contents
        )

    # resolve includes
    for include in soup.find_all("include"):
        include.replace_with(
            *resolve_recursively(
                open(include.args[0]).read().strip(), file_path
            ).contents
        )

    # resolve inputs
    for _input in soup.find_all("input"):
        file_name = os.path.join(directory, _input.contents[0] + ".tex")
        _input.replace_with(
            *resolve_recursively(open(file_name).read().strip(), file_path).contents
        )

    return soup


def resolve(file_path):
    new_soup = resolve_recursively(open(file_path).read().strip(), file_path)

    with open(file_path, "w") as f:
        f.write(repr(new_soup))
